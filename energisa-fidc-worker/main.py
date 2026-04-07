"""
FIDC Compute Worker — FastAPI
Endpoint assíncrono: recebe sessionId, lista arquivos do Supabase Storage,
processa com Pandas vetorizado, salva CSV no Storage e registra status em
fidc_compute_jobs.
"""
from __future__ import annotations

import io
import os
import uuid
from typing import Literal, Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client

from calculator_vectorized import (
    calculate_vectorized,
    get_ipca_monthly,
    get_di_pre_rate,
)

load_dotenv()

SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
BUCKET             = "temp"
FETCH_BATCH_SIZE   = 2_000   # linhas por requisição REST (I/O)

# Colunas brutas lidas do DB
RAW_COLS = (
    "id,row_number,file_name,empresa,tipo,status_conta,situacao,"
    "nome_cliente,documento,classe,contrato,"
    "valor_principal,valor_nao_cedido,valor_terceiro,valor_cip,"
    "data_vencimento,data_base,base_origem,is_voltz"
)

# Ordem das colunas no CSV de saída
CSV_COLS = [
    "row_number", "file_name", "empresa", "tipo", "status_conta", "situacao",
    "nome_cliente", "documento", "classe", "contrato",
    "valor_principal", "valor_nao_cedido", "valor_terceiro", "valor_cip",
    "data_vencimento", "data_base", "base_origem", "is_voltz",
    "dias_atraso", "aging", "aging_taxa",
    "valor_liquido", "multa", "juros_moratorios", "fator_correcao",
    "correcao_monetaria", "valor_corrigido",
    "juros_remuneratorios", "saldo_devedor_vencimento",
    "taxa_recuperacao", "prazo_recebimento", "valor_recuperavel", "valor_justo",
]

CSV_HEADER_PT = [
    "Nº Linha", "Arquivo", "Empresa", "Tipo", "Status", "Situação",
    "Nome Cliente", "CPF/CNPJ", "Classe", "Contrato",
    "Valor Principal", "Vlr Não Cedido", "Vlr Terceiros", "Vlr CIP",
    "Data Vencimento", "Data Base", "Base Origem", "É Voltz",
    "Dias Atraso", "Aging", "Aging Taxa",
    "Valor Líquido", "Multa 2%", "Juros Moratórios", "Fator Correção",
    "Correção Monetária", "Valor Corrigido",
    "Juros Remun.", "SDV",
    "Taxa Recuperação", "Prazo Receb.", "Valor Recuperável", "Valor Justo",
]


# ─── Supabase client ──────────────────────────────────────────────────

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ─── CSV helpers ──────────────────────────────────────────────────────

def _fmt_float(v) -> str:
    if pd.isna(v):
        return ""
    return f"{float(v):.2f}".replace(".", ",")


def _build_csv(result_df: pd.DataFrame) -> str:
    """Constrói CSV semicolon-separated com formatação pt-BR."""
    out = result_df.reindex(columns=CSV_COLS).copy()

    # Booleano → Sim / Não
    if "is_voltz" in out.columns:
        out["is_voltz"] = out["is_voltz"].map(
            lambda v: "Sim" if v is True or v == 1 else "Não"
        )

    # Floats → formato brasileiro (2 casas, vírgula decimal)
    float_cols = [
        "valor_principal", "valor_nao_cedido", "valor_terceiro", "valor_cip",
        "valor_liquido", "multa", "juros_moratorios", "fator_correcao",
        "correcao_monetaria", "valor_corrigido",
        "juros_remuneratorios", "saldo_devedor_vencimento",
        "taxa_recuperacao", "valor_recuperavel", "valor_justo",
    ]
    for col in float_cols:
        if col in out.columns:
            out[col] = out[col].apply(_fmt_float)

    # Strings — escapa ponto-e-vírgula
    for col in out.select_dtypes(include="object").columns:
        out[col] = out[col].fillna("").astype(str).str.replace(";", ",", regex=False)

    buf = io.StringIO()
    out.to_csv(buf, sep=";", index=False, header=CSV_HEADER_PT, lineterminator="\r\n")
    return buf.getvalue()


# ─── Background job ───────────────────────────────────────────────────

def compute_job(job_id: str, session_id: str) -> None:
    sb = get_supabase()

    def update_job(**kwargs) -> None:
        sb.table("fidc_compute_jobs").update(kwargs).eq("id", job_id).execute()

    try:
        update_job(status="processing")

        # ── 1. Parâmetros da sessão ─────────────────────────────
        sess = (
            sb.table("fidc_sessions")
            .select("metadata")
            .eq("id", session_id)
            .single()
            .execute()
        )
        metadata        = (sess.data or {}).get("metadata") or {}
        spread_percent  = float(metadata.get("spread_percent",  0.025))
        prazo_horizonte = int(metadata.get("prazo_horizonte",   6))

        # ── 2. Listar arquivos de origem no Storage ─────────────
        # Pasta onde os CSVs convertidos ficam após validação
        try:
            storage_files = sb.storage.from_(BUCKET).list(f"validados/{session_id}")
            source_files = [
                f["name"] for f in (storage_files or [])
                if f.get("name") and not f["name"].startswith("fidc_resultados_")
            ]
        except Exception:
            source_files = []

        # ── 3. Tabelas de referência do banco ───────────────────
        indices = (
            sb.table("fidc_indices")
            .select("date,value")
            .eq("session_id", session_id)
            .execute()
            .data or []
        )
        recovery_rates = (
            sb.table("fidc_recovery_rates")
            .select("empresa,tipo,aging,taxa_recuperacao,prazo_recebimento")
            .eq("session_id", session_id)
            .execute()
            .data or []
        )
        di_pre_rates = (
            sb.table("fidc_di_pre_rates")
            .select("meses_futuros,taxa_252")
            .eq("session_id", session_id)
            .execute()
            .data or []
        )

        # ── 4. Conta linhas totais ──────────────────────────────
        count_resp = (
            sb.table("fidc_session_data")
            .select("id", count="exact")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        total = count_resp.count or 0
        update_job(rows_total=total)

        # ── 5. Busca TODOS os dados em lotes (I/O) → lista ─────
        all_rows: list[dict] = []
        page = 0
        while len(all_rows) < total:
            batch = (
                sb.table("fidc_session_data")
                .select(RAW_COLS)
                .eq("session_id", session_id)
                .order("row_number")
                .range(page * FETCH_BATCH_SIZE, (page + 1) * FETCH_BATCH_SIZE - 1)
                .execute()
                .data or []
            )
            if not batch:
                break
            all_rows.extend(batch)
            page += 1
            # Progresso parcial durante a fase de leitura
            update_job(rows_done=min(len(all_rows), total))

        # ── 6. Cálculo vetorizado (Pandas / NumPy) ──────────────
        df = pd.DataFrame(all_rows)
        result_df = calculate_vectorized(
            df, indices, recovery_rates, di_pre_rates,
            spread_percent, prazo_horizonte,
        )

        # ── 7. Gera CSV em memória ──────────────────────────────
        csv_content = _build_csv(result_df)
        bom_content = "\ufeff" + csv_content   # BOM para compatibilidade Excel

        # ── 8. Upload para Supabase Storage ────────────────────
        file_name    = f"fidc_resultados_{session_id}.csv"
        storage_path = f"validados/{session_id}/{file_name}"

        sb.storage.from_(BUCKET).upload(
            storage_path,
            bom_content.encode("utf-8"),
            {"content-type": "text/csv;charset=utf-8", "x-upsert": "true"},
        )

        public_url = sb.storage.from_(BUCKET).get_public_url(storage_path)
        update_job(
            status="done",
            csv_url=public_url,
            rows_done=total,
        )

    except Exception as exc:
        update_job(status="error", error_message=str(exc))
        raise


# ─── FastAPI app ──────────────────────────────────────────────────────

# CORS origins configurados via env (ex: "https://app.vercel.app,https://staging.vercel.app")
_CORS_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
_CORS_ORIGINS_SET = set(o.strip() for o in _CORS_ORIGINS)
_CORS_ALLOW_ALL = "*" in _CORS_ORIGINS_SET

# Instância interna do FastAPI — todas as rotas são registradas aqui.
# NÃO adicionar CORSMiddleware via add_middleware: o Starlette coloca o
# CORSMiddleware DENTRO do ServerErrorMiddleware, então respostas 500 não
# atravessam o wrapper de send do CORSMiddleware e saem sem CORS headers.
_app = FastAPI(title="FIDC Compute Worker", version="2.0.0")


def _make_cors_headers(origin: str) -> dict[str, str]:
    """Retorna os headers CORS a serem incluídos em qualquer resposta."""
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Vary": "Origin",
    }


def _allowed_origin(origin: str) -> str | None:
    """Retorna a origin permitida ou None se não permitida."""
    if not origin:
        return None
    if _CORS_ALLOW_ALL or origin in _CORS_ORIGINS_SET:
        return origin
    return None


@_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler de exceções não-tratadas. Retorna JSON 500 com CORS headers.
    Nota: este handler é passado ao ServerErrorMiddleware como .handler,
    e o ServerErrorMiddleware envia a resposta pelo send raw (bypass do
    CORSMiddleware interno). Por isso os headers CORS são adicionados
    manualmente aqui E o CORSMiddleware externo (wrap abaixo) os reforça.
    """
    origin = request.headers.get("origin", "")
    allowed = _allowed_origin(origin)
    headers = _make_cors_headers(allowed) if allowed else {}
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers=headers,
    )


# ── Alias para registrar as rotas (decorators usam `app`) ─────────────
app = _app


class ComputeRequest(BaseModel):
    session_id: str


class JobStatus(BaseModel):
    job_id:     str
    status:     Literal["pending", "processing", "done", "error"]
    rows_total: Optional[int]   = None
    rows_done:  Optional[int]   = None
    csv_url:    Optional[str]   = None
    error:      Optional[str]   = None


def _row_to_job_status(d: dict) -> JobStatus:
    return JobStatus(
        job_id     = d["id"],
        status     = d["status"],
        rows_total = d.get("rows_total"),
        rows_done  = d.get("rows_done"),
        csv_url    = d.get("csv_url"),
        error      = d.get("error_message"),
    )


@app.post("/compute", response_model=JobStatus)
def start_compute(req: ComputeRequest, background_tasks: BackgroundTasks):
    """
    Dispara o cálculo vetorizado em background.
    Retorna imediatamente com job_id para polling.
    """
    sb     = get_supabase()
    job_id = str(uuid.uuid4())

    sb.table("fidc_compute_jobs").insert({
        "id":         job_id,
        "session_id": req.session_id,
        "status":     "pending",
    }).execute()

    background_tasks.add_task(compute_job, job_id, req.session_id)
    return JobStatus(job_id=job_id, status="pending")


@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str):
    """Retorna o status atual de um job (polling)."""
    sb   = get_supabase()
    resp = (
        sb.table("fidc_compute_jobs")
        .select("*")
        .eq("id", job_id)
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return _row_to_job_status(resp.data)


@app.get("/sessions/{session_id}/job", response_model=Optional[JobStatus])
def get_latest_session_job(session_id: str):
    """
    Retorna o job mais recente para uma sessão (ou null se não houver).
    Usado pelo frontend para recuperar csv_url após navegação entre páginas.
    """
    sb   = get_supabase()
    resp = (
        sb.table("fidc_compute_jobs")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return None
    return _row_to_job_status(resp.data[0])


@app.get("/health")
def health():
    return {"ok": True}


# ── CORS outermost wrap ────────────────────────────────────────────────
#
# O CORSMiddleware é aplicado FORA do FastAPI/Starlette, envolvendo o
# objeto `app` já construído (com ServerErrorMiddleware incluído).
# Resultado: a pilha de middleware vista pelo uvicorn é:
#
#   CORSMiddleware          ← envolve send ANTES de tudo
#     └── ServerErrorMiddleware
#           └── ExceptionMiddleware → rotas
#
# Assim, QUALQUER resposta — incluindo 500s gerados pelo
# ServerErrorMiddleware — passa pelo wrapper de send do CORSMiddleware
# e recebe os headers Access-Control-Allow-Origin corretos.
#
# Referência: Starlette issue #1116 — "Errors are not reported using
# CORS middleware" (merged fix pattern).
#
# uvicorn main:app  →  app = CORSMiddleware(FastAPI(...))  ✓
app = CORSMiddleware(
    app=app,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
