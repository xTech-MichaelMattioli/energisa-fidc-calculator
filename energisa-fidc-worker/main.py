"""
FIDC Compute Worker — FastAPI
Endpoint assíncrono: recebe sessionId, lê CSVs diretamente do Supabase Storage
(paths armazenados em fidc_sessions.metadata.files), processa com Pandas
vetorizado, salva CSV resultado no Storage e registra status + summary em
fidc_compute_jobs.
"""
from __future__ import annotations

import io
import os
import uuid
from typing import Any, Literal, Optional

import pandas as pd
import numpy as np
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client

from calculator_vectorized import (
    calculate_vectorized,
    compute_summary,
    get_ipca_monthly,
    get_di_pre_rate,
)

load_dotenv()

SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
BUCKET               = "temp"

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


# ─── CSV parsing helpers ──────────────────────────────────────────────

def _download_csv(sb: Client, path: str) -> pd.DataFrame:
    """Baixa um arquivo do Storage e retorna como DataFrame (dtype=str)."""
    raw: bytes = sb.storage.from_(BUCKET).download(path)
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(
                io.BytesIO(raw),
                sep=None,
                engine="python",
                encoding=encoding,
                dtype=str,
                on_bad_lines="skip",
                low_memory=False,
            )
        except Exception:
            continue
    raise ValueError(f"Não foi possível parsear CSV: {path}")


def _parse_float_col(series: pd.Series) -> pd.Series:
    """Parse de coluna numérica: aceita formato pt-BR (1.234,56) e padrão."""
    s = series.astype(str).str.strip()
    result = pd.to_numeric(s, errors="coerce")
    na_mask = result.isna()
    if na_mask.any():
        br = pd.to_numeric(
            s[na_mask]
            .str.replace(r"\s", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False),
            errors="coerce",
        )
        result[na_mask] = br
    return result.fillna(0.0)


def _parse_date_col(series: pd.Series) -> pd.Series:
    """Parse de coluna de data: aceita ISO (YYYY-MM-DD) e BR (DD/MM/YYYY)."""
    s = series.astype(str).str.strip()
    # ISO format
    parsed = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    # BR format para os que ficaram NaT
    br_mask = parsed.isna()
    if br_mask.any():
        parsed[br_mask] = pd.to_datetime(s[br_mask], format="%d/%m/%Y", errors="coerce")
    # fallback genérico
    still_na = parsed.isna()
    if still_na.any():
        parsed[still_na] = pd.to_datetime(s[still_na], dayfirst=True, errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), other=None)


# ─── Background job ───────────────────────────────────────────────────

def compute_job(job_id: str, session_id: str) -> None:
    sb = get_supabase()

    def update_job(**kwargs) -> None:
        sb.table("fidc_compute_jobs").update(kwargs).eq("id", job_id).execute()

    try:
        update_job(status="processing")

        # ── 1. Parâmetros da sessão ─────────────────────────────────
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
        data_base_global = str(metadata.get("data_base", ""))
        files_meta: list[dict] = metadata.get("files", [])

        if not files_meta:
            raise ValueError(
                "Nenhum arquivo encontrado em fidc_sessions.metadata.files. "
                "Certifique-se de usar a versão atualizada do frontend."
            )

        # ── 2. Tabelas de referência ────────────────────────────────
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

        # ── 3. Baixa e parseia CSVs do Storage ──────────────────────
        all_dfs: list[pd.DataFrame] = []
        row_counter = 1

        for file_info in files_meta:
            file_name    = file_info.get("name", "unknown")
            is_voltz_f   = bool(file_info.get("is_voltz", False))
            field_mapping: dict = file_info.get("field_mapping", {})
            paths: list[str]    = file_info.get("paths", [])

            chunks: list[pd.DataFrame] = []
            for path in paths:
                if not path:
                    continue
                try:
                    chunk_df = _download_csv(sb, path)
                    chunks.append(chunk_df)
                except Exception as e:
                    print(f"[WARN] Falha ao baixar {path}: {e}")
                    continue

            if not chunks:
                print(f"[WARN] Nenhum chunk baixado para {file_name}")
                continue

            file_df = pd.concat(chunks, ignore_index=True)

            # Renomeia colunas: {internal_name: csv_col} → {csv_col: internal_name}
            rename_map = {csv_col: internal for internal, csv_col in field_mapping.items() if csv_col}
            file_df = file_df.rename(columns=rename_map)

            # Metadados por arquivo
            file_df["file_name"] = file_name
            file_df["is_voltz"]  = is_voltz_f

            # data_base: usa coluna do CSV se existir, senão o global da sessão
            if "data_base" not in file_df.columns or file_df["data_base"].isna().all():
                file_df["data_base"] = data_base_global

            # base_origem: usa coluna do CSV se existir, senão o nome do arquivo
            if "base_origem" not in file_df.columns:
                file_df["base_origem"] = file_name

            # Numeração de linhas contínua entre arquivos
            n = len(file_df)
            file_df["row_number"] = range(row_counter, row_counter + n)
            row_counter += n

            all_dfs.append(file_df)

        if not all_dfs:
            raise ValueError("Nenhum dado lido dos arquivos. Verifique os caminhos no metadata da sessão.")

        df = pd.concat(all_dfs, ignore_index=True)
        total = len(df)
        update_job(rows_total=total)

        # ── 4. Coerção de tipos ─────────────────────────────────────
        for col in ["valor_principal", "valor_nao_cedido", "valor_terceiro", "valor_cip"]:
            if col in df.columns:
                df[col] = _parse_float_col(df[col])
            else:
                df[col] = 0.0

        for col in ["data_vencimento", "data_base"]:
            if col in df.columns:
                df[col] = _parse_date_col(df[col])

        # is_voltz: garante booleano
        df["is_voltz"] = df["is_voltz"].map(
            lambda v: True if v is True or str(v).lower() in ("true", "1", "sim") else False
        )

        # ── 5. Cálculo vetorizado ───────────────────────────────────
        result_df = calculate_vectorized(
            df, indices, recovery_rates, di_pre_rates,
            spread_percent, prazo_horizonte,
        )

        # ── 6. Summary para os cards do frontend ────────────────────
        summary = compute_summary(result_df)

        # ── 7. Gera CSV em memória ──────────────────────────────────
        csv_content = _build_csv(result_df)
        bom_content = "\ufeff" + csv_content   # BOM para Excel

        # ── 8. Upload para Supabase Storage ────────────────────────
        out_file_name = f"fidc_resultados_{session_id}.csv"
        storage_path  = f"validados/{session_id}/{out_file_name}"

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
            summary=summary,
        )

    except Exception as exc:
        update_job(status="error", error_message=str(exc))
        raise


# ─── FastAPI app ──────────────────────────────────────────────────────

_CORS_ORIGINS     = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
_CORS_ORIGINS_SET = set(o.strip() for o in _CORS_ORIGINS)
_CORS_ALLOW_ALL   = "*" in _CORS_ORIGINS_SET

_app = FastAPI(title="FIDC Compute Worker", version="3.0.0")


def _make_cors_headers(origin: str) -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin":  origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Vary": "Origin",
    }


def _allowed_origin(origin: str) -> str | None:
    if not origin:
        return None
    if _CORS_ALLOW_ALL or origin in _CORS_ORIGINS_SET:
        return origin
    return None


@_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin  = request.headers.get("origin", "")
    allowed = _allowed_origin(origin)
    headers = _make_cors_headers(allowed) if allowed else {}
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers=headers,
    )


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
    summary:    Optional[Any]   = None   # FidcSummary-compatible dict


def _row_to_job_status(d: dict) -> JobStatus:
    return JobStatus(
        job_id     = d["id"],
        status     = d["status"],
        rows_total = d.get("rows_total"),
        rows_done  = d.get("rows_done"),
        csv_url    = d.get("csv_url"),
        error      = d.get("error_message"),
        summary    = d.get("summary"),
    )


@app.post("/compute", response_model=JobStatus)
def start_compute(req: ComputeRequest, background_tasks: BackgroundTasks):
    """Dispara o cálculo vetorizado em background. Retorna job_id para polling."""
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
    """Retorna o job mais recente de uma sessão (ou null). Usado para recuperar csv_url + summary após navegação."""
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


# ── CORSMiddleware como camada mais externa (Starlette issue #1116) ───
app = CORSMiddleware(
    app=app,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
