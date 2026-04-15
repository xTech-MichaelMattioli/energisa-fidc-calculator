"""
FIDC Calculator v2 — Interface Streamlit
=========================================
Aplicação single-page com 4 abas:
  📁 Arquivos   — upload + mapeamento de colunas
  ⚙️  Parâmetros — data base, spread, índices, taxas, DI-PRE
  ▶️  Calcular   — executa cálculo vetorizado com progresso
  📊 Resultados — métricas, tabelas, exportação

Como rodar:
    cd energisa-fidc-calculator-distrib/v2
    streamlit run app.py
"""

import gc
import time
from datetime import date, datetime

import numpy as np
import pandas as pd
import streamlit as st

import engine as eng

# ══════════════════════════════════════════════════════════════════════
# CONFIG DA PÁGINA
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="FIDC Calculator v2",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    [data-testid="stMetricValue"] { font-size: 1.1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _cur(v: float) -> str:
    return f"R$ {v:_.2f}".replace(".", ",").replace("_", ".")

def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"

def _init_state():
    defaults = {
        "files_data":        [],   # list of {name, df_raw, mapping}
        "df_taxa":           None,
        "df_di_pre":         None,
        "df_indices_excel":  None,
        "idx_df":            None,
        "ipca_dict":         None,
        "df_result":         None,
        "summary":           None,
        "calc_done":         False,
        "params": {
            "data_base":        date.today().strftime("%Y-%m-%d"),
            "spread_percent":   0.025,
            "prazo_horizonte":  6,
            "is_voltz_global":  False,
            "use_builtin_idx":  True,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ══════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════

st.title("⚡ FIDC Calculator v2")

tab_upload, tab_params, tab_calc, tab_results = st.tabs([
    "📁 Arquivos",
    "⚙️ Parâmetros",
    "▶️ Calcular",
    "📊 Resultados",
])

# ══════════════════════════════════════════════════════════════════════
# ABA 1 — UPLOAD + MAPEAMENTO
# ══════════════════════════════════════════════════════════════════════

with tab_upload:
    st.subheader("1. Carregar Arquivos de Dados")

    col_up, col_info = st.columns([2, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Arraste os arquivos ou clique para selecionar",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
            help="Suporta Excel (.xlsx/.xls) e CSV. Múltiplos arquivos aceitos.",
        )

    with col_info:
        st.info(
            "**Formatos aceitos**\n"
            "- Excel (.xlsx / .xls)\n"
            "- CSV (qualquer separador)\n"
            "- Encoding: UTF-8, Latin-1, CP1252\n\n"
            "**Múltiplos arquivos** são concatenados automaticamente."
        )

    if uploaded:
        st.markdown("---")
        st.subheader("2. Mapeamento de Colunas")
        st.caption("O sistema detecta os campos automaticamente. Ajuste os que ficaram em branco.")

        new_files_data = []

        for up_file in uploaded:
            with st.expander(f"📄 {up_file.name}", expanded=True):
                try:
                    df_raw = eng.read_uploaded_file(up_file)
                except Exception as e:
                    st.error(f"Erro ao ler {up_file.name}: {e}")
                    continue

                st.caption(f"{len(df_raw):,} linhas · {len(df_raw.columns)} colunas")

                # Preview (checkbox evita expander aninhado — não suportado pelo Streamlit)
                if st.checkbox("👁️ Pré-visualizar dados (5 linhas)", key=f"prev_{up_file.name}"):
                    st.dataframe(df_raw.head(5), use_container_width=True)

                csv_cols  = list(df_raw.columns)
                detected  = eng.auto_detect_columns(csv_cols)

                ALL_INTERNAL = (
                    eng.REQUIRED_COLS
                    + eng.IMPORTANT_COLS
                    + [
                        "valor_nao_cedido", "valor_terceiro", "valor_cip",
                        "tipo", "nome_cliente", "documento",
                        "contrato", "classe", "situacao", "status_conta",
                        "is_voltz",
                    ]
                )

                # Status da detecção
                ok  = [c for c in ALL_INTERNAL if c in detected]
                nok = [c for c in ALL_INTERNAL if c not in detected]

                c1, c2 = st.columns(2)
                c1.success(f"✓ {len(ok)} campos detectados")
                c2.warning(f"○ {len(nok)} campos não detectados")

                # Tabela de mapeamento
                st.markdown("**Confirme o mapeamento:**")
                mapping = {}
                opts = ["— não usar —"] + csv_cols

                cols_per_row = 3
                internal_list = ALL_INTERNAL
                for i in range(0, len(internal_list), cols_per_row):
                    row_cols = st.columns(cols_per_row)
                    for j, internal in enumerate(internal_list[i : i + cols_per_row]):
                        current = detected.get(internal, "")
                        is_req  = internal in eng.REQUIRED_COLS
                        label   = f"{'🔴 ' if is_req else ''}{internal}"
                        sel = row_cols[j].selectbox(
                            label,
                            options=opts,
                            index=opts.index(current) if current in opts else 0,
                            key=f"map_{up_file.name}_{internal}",
                        )
                        if sel != "— não usar —":
                            mapping[internal] = sel

                # Verifica obrigatórios
                missing = [c for c in eng.REQUIRED_COLS if c not in mapping]
                if missing:
                    st.error(f"🔴 Campos obrigatórios não mapeados: {', '.join(missing)}")
                else:
                    st.success("✅ Todos os campos obrigatórios mapeados!")

                new_files_data.append({
                    "name":    up_file.name,
                    "df_raw":  df_raw,
                    "mapping": mapping,
                })

        st.session_state.files_data = new_files_data
        st.session_state.calc_done  = False

        if new_files_data:
            total_rows = sum(len(f["df_raw"]) for f in new_files_data)
            st.success(f"✅ {len(new_files_data)} arquivo(s) · {total_rows:,} linhas prontas para cálculo.")

    elif not st.session_state.files_data:
        st.info("⬆️ Faça upload de pelo menos um arquivo para começar.")

# ══════════════════════════════════════════════════════════════════════
# ABA 2 — PARÂMETROS
# ══════════════════════════════════════════════════════════════════════

with tab_params:
    st.subheader("Parâmetros de Cálculo")

    p = st.session_state.params

    # ── Parâmetros básicos ────────────────────────────────────────────
    with st.expander("📅 Parâmetros Gerais", expanded=True):
        c1, c2, c3, c4 = st.columns(4)

        raw_date = c1.date_input(
            "Data Base",
            value=datetime.strptime(p["data_base"], "%Y-%m-%d").date(),
        )
        p["data_base"] = raw_date.strftime("%Y-%m-%d")

        p["spread_percent"] = c2.number_input(
            "Spread (%)",
            min_value=0.0, max_value=20.0,
            value=p["spread_percent"] * 100,
            step=0.1,
            format="%.2f",
        ) / 100

        p["prazo_horizonte"] = c3.number_input(
            "Prazo Horizonte (meses)",
            min_value=1, max_value=60,
            value=p["prazo_horizonte"],
            step=1,
        )

        p["is_voltz_global"] = c4.checkbox(
            "⚡ Todos são VOLTZ",
            value=p["is_voltz_global"],
            help="Marca todos os registros como VOLTZ independente do nome do arquivo.",
        )

    # ── Índices Econômicos ────────────────────────────────────────────
    with st.expander("📈 Índices Econômicos (IGP-M / IPCA)", expanded=True):
        st.caption(
            "Série acumulada mensal usada para o **fator de correção monetária**. "
            "IGP-M está embutido até mai/2021; IPCA pós-2021 é buscado do IBGE automaticamente."
        )

        idx_mode = st.radio(
            "Fonte dos índices",
            ["Embutido (IGP-M + IPCA IBGE)", "Carregar do Excel"],
            horizontal=True,
        )
        p["use_builtin_idx"] = idx_mode == "Embutido (IGP-M + IPCA IBGE)"

        if p["use_builtin_idx"]:
            if st.button("🔄 Carregar IPCA do IBGE (internet)", use_container_width=False):
                with st.spinner("Buscando IPCA do IBGE SIDRA..."):
                    ipca = eng.load_ipca_from_sidra()
                    st.session_state.ipca_dict   = ipca
                    st.session_state.idx_df      = eng.build_index_series(
                        igpm_dict=eng.IGPM_DICT, ipca_dict=ipca
                    )
                st.success(f"✅ {len(ipca)} pontos IPCA carregados.")

            # Se ainda não carregou, usa fallback
            if st.session_state.idx_df is None:
                st.session_state.idx_df = eng.build_index_series()
                st.info("ℹ️ Usando índices embutidos (IGP-M até mai/2021 + IPCA fallback).")

            if st.session_state.idx_df is not None:
                df_idx = st.session_state.idx_df
                col = "value" if "value" in df_idx.columns else "indice"
                dt_col = "date" if "date" in df_idx.columns else "data"
                st.caption(
                    f"Série: {df_idx[dt_col].min().strftime('%Y-%m')} → "
                    f"{df_idx[dt_col].max().strftime('%Y-%m')} "
                    f"({len(df_idx)} pontos)"
                )

        else:
            idx_file = st.file_uploader(
                "Arquivo de índices (.xlsx)",
                type=["xlsx", "xls"],
                key="idx_file",
                help="Estrutura: Aba IGPM_IPCA (colunas C=Ano, D=Mês, F=Índice) "
                     "ou aba IGPM (col A=Data, col B=Índice).",
            )
            if idx_file:
                sheet = st.text_input("Aba específica (deixe em branco para usar a primeira)", value="")
                if st.button("📥 Carregar índices", key="btn_load_idx"):
                    with st.spinner("Lendo arquivo..."):
                        df_idx_excel = eng.load_indices_from_excel(idx_file, sheet or None)
                    if df_idx_excel is not None and not df_idx_excel.empty:
                        st.session_state.df_indices_excel = df_idx_excel
                        st.session_state.idx_df = eng.build_index_series(df_excel=df_idx_excel)
                        st.success(
                            f"✅ {len(df_idx_excel)} pontos carregados "
                            f"({df_idx_excel['data'].min().strftime('%Y-%m')} → "
                            f"{df_idx_excel['data'].max().strftime('%Y-%m')})"
                        )
                    else:
                        st.error("❌ Não foi possível ler o arquivo de índices.")

    # ── Taxas de Recuperação ──────────────────────────────────────────
    with st.expander("💰 Taxas de Recuperação", expanded=True):
        st.caption(
            "Tabela com taxa (%) e prazo (meses) por **Empresa × Tipo × Aging**. "
            "Para VOLTZ: tabela padrão já embutida."
        )
        taxa_file = st.file_uploader(
            "Arquivo de taxas (.xlsx / .xls)",
            type=["xlsx", "xls"],
            key="taxa_file",
        )
        if taxa_file:
            if st.button("📥 Carregar taxas", key="btn_taxa"):
                with st.spinner("Lendo taxas de recuperação..."):
                    df_taxa = eng.load_recovery_rates_from_excel(taxa_file)
                if df_taxa is not None and not df_taxa.empty:
                    st.session_state.df_taxa = df_taxa
                    st.success(f"✅ {len(df_taxa)} registros de taxa carregados.")
                    st.dataframe(df_taxa.head(10), use_container_width=True)
                else:
                    st.error("❌ Erro ao ler arquivo de taxas.")

        if st.session_state.df_taxa is not None:
            st.caption(f"✅ {len(st.session_state.df_taxa)} taxas na memória.")
        else:
            st.info("⚠️ Sem taxas carregadas — VOLTZ usa defaults embutidos, demais: taxa = 0.")

    # ── DI-PRE ────────────────────────────────────────────────────────
    with st.expander("📉 Curva DI-PRE", expanded=True):
        st.caption(
            "Curva de juros futuros (DI × Pré) para o **fator de desconto** do valor justo. "
            "Colunas: `meses_futuros` e `252` (taxa % a.a.)."
        )

        di_mode = st.radio(
            "Fonte DI-PRE",
            ["Manual", "Carregar arquivo"],
            horizontal=True,
            key="di_mode",
        )

        if di_mode == "Manual":
            c1, c2 = st.columns(2)
            taxa_manual = c1.number_input(
                "Taxa DI-PRE (% a.a.)",
                min_value=0.0, max_value=50.0,
                value=12.0, step=0.1,
            )
            prazo_manual = c2.number_input(
                "Para o prazo (meses)",
                min_value=1, max_value=60,
                value=int(p["prazo_horizonte"]),
            )
            if st.button("✅ Confirmar taxa", key="btn_di_manual"):
                st.session_state.df_di_pre = pd.DataFrame([{
                    "meses_futuros": prazo_manual,
                    "252": taxa_manual,
                }])
                st.success(f"✅ DI-PRE: {taxa_manual:.2f}% a.a. para {prazo_manual} meses.")
        else:
            di_file = st.file_uploader(
                "Arquivo DI-PRE (.xlsx)",
                type=["xlsx", "xls"],
                key="di_file",
            )
            if di_file:
                if st.button("📥 Carregar DI-PRE", key="btn_di_file"):
                    with st.spinner("Lendo curva DI-PRE..."):
                        df_di = eng.load_di_pre_from_excel(di_file)
                    if df_di is not None and not df_di.empty:
                        st.session_state.df_di_pre = df_di
                        st.success(f"✅ {len(df_di)} pontos da curva carregados.")
                        st.dataframe(df_di, use_container_width=True)
                    else:
                        st.error("❌ Erro ao ler arquivo DI-PRE.")

        if st.session_state.df_di_pre is not None:
            st.caption(f"✅ DI-PRE na memória: {len(st.session_state.df_di_pre)} ponto(s).")
        else:
            st.info("ℹ️ Sem DI-PRE — será usado 12% a.a. como padrão.")

    st.session_state.params = p

# ══════════════════════════════════════════════════════════════════════
# ABA 3 — CALCULAR
# ══════════════════════════════════════════════════════════════════════

with tab_calc:
    st.subheader("Executar Cálculo Vetorizado")

    files_data = st.session_state.files_data
    p          = st.session_state.params

    # Checklist pré-cálculo
    checks = {
        "Arquivos carregados":         len(files_data) > 0,
        "Índices econômicos prontos":  st.session_state.idx_df is not None,
    }
    all_ok = all(checks.values())

    c_check, c_btn = st.columns([2, 1])
    with c_check:
        for label, ok in checks.items():
            icon = "✅" if ok else "❌"
            st.write(f"{icon} {label}")

    if not checks["Arquivos carregados"]:
        st.warning("⬅️ Volte à aba **Arquivos** e faça o upload dos dados.")
    if not checks["Índices econômicos prontos"]:
        st.warning("⬅️ Volte à aba **Parâmetros** e carregue/confirme os índices.")

    # Parâmetros resumidos
    with st.expander("📋 Parâmetros que serão usados", expanded=False):
        st.json({
            "data_base":        p["data_base"],
            "spread_percent":   f"{p['spread_percent']*100:.2f}%",
            "prazo_horizonte":  f"{p['prazo_horizonte']} meses",
            "is_voltz_global":  p["is_voltz_global"],
            "indices":          "Excel personalizado" if not p["use_builtin_idx"] else "Embutido (IGP-M + IPCA)",
            "di_pre":           f"{len(st.session_state.df_di_pre)} ponto(s)" if st.session_state.df_di_pre is not None else "padrão 12%",
            "taxa_recuperacao": f"{len(st.session_state.df_taxa)} registros" if st.session_state.df_taxa is not None else "VOLTZ defaults / zero",
        })

    st.markdown("---")

    if all_ok:
        if st.button("⚡ CALCULAR AGORA", type="primary", use_container_width=True):
            t_start = time.time()

            progress = st.progress(0, text="Preparando...")
            status   = st.empty()

            try:
                all_results: list[pd.DataFrame] = []
                total_files = len(files_data)

                for i, fd in enumerate(files_data):
                    fname   = fd["name"]
                    df_raw  = fd["df_raw"]
                    mapping = fd["mapping"]

                    pct = int((i / total_files) * 80)
                    progress.progress(pct, text=f"Processando {fname}...")
                    status.info(f"📄 {fname} — {len(df_raw):,} linhas")

                    # Renomear colunas conforme mapeamento
                    rename_map = {v: k for k, v in mapping.items()}
                    df = df_raw.rename(columns=rename_map).copy()

                    # Detectar VOLTZ pelo nome do arquivo
                    is_voltz_file = "VOLTZ" in fname.upper()
                    if is_voltz_file and "is_voltz" not in df.columns:
                        df["is_voltz"] = True

                    # Garantir coluna empresa se mapeada
                    if "empresa" not in df.columns and is_voltz_file:
                        df["empresa"] = "VOLTZ"

                    # Cálculo vetorizado
                    result = eng.calculate(
                        df             = df,
                        idx_df         = st.session_state.idx_df,
                        df_taxa        = st.session_state.df_taxa,
                        df_di_pre      = st.session_state.df_di_pre,
                        data_base      = p["data_base"],
                        spread_percent = p["spread_percent"],
                        prazo_horizonte= p["prazo_horizonte"],
                        is_voltz_global= p["is_voltz_global"],
                    )
                    result["__source_file__"] = fname
                    all_results.append(result)
                    del df, result
                    gc.collect()

                progress.progress(85, text="Concatenando resultados...")

                df_final = pd.concat(all_results, ignore_index=True)
                del all_results
                gc.collect()

                progress.progress(95, text="Calculando resumo...")
                summary = eng.compute_summary(df_final)

                st.session_state.df_result = df_final
                st.session_state.summary   = summary
                st.session_state.calc_done = True

                elapsed = time.time() - t_start
                progress.progress(100, text="Concluído!")
                status.success(
                    f"✅ **{summary['total_rows']:,} linhas** calculadas em **{elapsed:.1f}s** · "
                    f"Valor Justo total: **{_cur(summary['total_valor_justo'])}**"
                )

                st.balloons()
                st.info("➡️ Veja os resultados na aba **📊 Resultados**.")

            except Exception as exc:
                progress.empty()
                status.error(f"❌ Erro durante o cálculo: {exc}")
                import traceback
                st.code(traceback.format_exc())

    if st.session_state.calc_done:
        s = st.session_state.summary
        st.markdown("---")
        st.caption(f"Último cálculo: {s['total_rows']:,} linhas · Valor Justo: {_cur(s['total_valor_justo'])}")

# ══════════════════════════════════════════════════════════════════════
# ABA 4 — RESULTADOS
# ══════════════════════════════════════════════════════════════════════

with tab_results:
    if not st.session_state.calc_done or st.session_state.summary is None:
        st.info("▶️ Execute o cálculo na aba **Calcular** para ver os resultados.")
        st.stop()

    s      = st.session_state.summary
    df_res = st.session_state.df_result

    # ── Métricas Principais ───────────────────────────────────────────
    st.subheader("Métricas Gerais")

    vp  = s["total_valor_principal"]
    vl  = s["total_valor_liquido"]
    vc  = s["total_valor_corrigido"]
    vj  = s["total_valor_justo"]
    up_vc = ((vc / vp) - 1) * 100 if vp > 0 else 0
    up_vj = ((vj / vp) - 1) * 100 if vp > 0 else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Linhas",       f"{s['total_rows']:,}")
    m2.metric("Valor Principal",    _cur(vp))
    m3.metric("Valor Corrigido",    _cur(vc), f"{up_vc:+.1f}% vs VP")
    m4.metric("Valor Recuperável",  _cur(s["total_valor_recuperavel"]))
    m5.metric("Valor Justo",        _cur(vj), f"{up_vj:+.1f}% vs VP")

    st.markdown("---")

    # ── Componentes da Correção ───────────────────────────────────────
    st.subheader("Composição da Correção Monetária")
    comp_cols = st.columns(4)
    comp_cols[0].metric("Multa (2%)",           _cur(s["total_multa"]))
    comp_cols[1].metric("Juros Moratórios",     _cur(s["total_juros_moratorios"]))
    comp_cols[2].metric("Correção IGP-M/IPCA",  _cur(s["total_correcao_monetaria"]))
    comp_cols[3].metric("Valor Líquido Base",   _cur(vl))

    # ── Por Aging ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Por Faixa de Aging")

    aging_rows = []
    for label in eng.AGING_LABELS:
        d = s["by_aging"].get(label)
        if not d:
            continue
        pct_vp = d["valor_principal"] / vp * 100 if vp > 0 else 0
        pct_vj = d["valor_justo"] / vj * 100 if vj > 0 else 0
        aging_rows.append({
            "Aging":           label,
            "Qtd":             f"{d['count']:,}",
            "Vlr Principal":   _cur(d["valor_principal"]),
            "% VP":            f"{pct_vp:.1f}%",
            "Vlr Corrigido":   _cur(d["valor_corrigido"]),
            "Valor Justo":     _cur(d["valor_justo"]),
            "% VJ":            f"{pct_vj:.1f}%",
        })
    if aging_rows:
        st.dataframe(pd.DataFrame(aging_rows), use_container_width=True, hide_index=True)

    # ── Por Empresa ───────────────────────────────────────────────────
    if s.get("by_empresa"):
        st.markdown("---")
        st.subheader("Por Empresa")
        emp_rows = []
        for emp, d in sorted(s["by_empresa"].items()):
            emp_rows.append({
                "Empresa":       emp,
                "Qtd":           f"{d['count']:,}",
                "Vlr Principal": _cur(d["valor_principal"]),
                "Vlr Corrigido": _cur(d["valor_corrigido"]),
                "Valor Justo":   _cur(d["valor_justo"]),
            })
        st.dataframe(pd.DataFrame(emp_rows), use_container_width=True, hide_index=True)

    # ── Dados Detalhados ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Dados Detalhados")

    filter_aging = st.multiselect(
        "Filtrar por Aging",
        options=eng.AGING_LABELS,
        default=[],
        placeholder="Todos",
    )

    df_show = df_res.copy()
    if filter_aging:
        df_show = df_show[df_show["aging"].isin(filter_aging)]

    # Colunas de exibição
    display_cols = [c for c in eng.OUTPUT_COLS if c in df_show.columns]
    header_map   = dict(zip(eng.OUTPUT_COLS, eng.OUTPUT_HEADERS))

    df_display = df_show[display_cols].copy()
    df_display.columns = [header_map.get(c, c) for c in display_cols]

    # Formata floats para pt-BR na exibição
    float_cols_display = [
        "Valor Principal", "Vlr Não Cedido", "Vlr Terceiros", "Vlr CIP",
        "Valor Líquido", "Multa 2%", "Juros Moratórios", "Fator Correção",
        "Correção Monetária", "Valor Corrigido",
        "Juros Remun.", "SDV",
        "Taxa Recuperação", "Valor Recuperável", "Valor Justo",
    ]
    for col in float_cols_display:
        if col in df_display.columns:
            df_display[col] = pd.to_numeric(df_display[col], errors="coerce").map(
                lambda v: "" if pd.isna(v) else f"{v:,.2f}"
            )

    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
    st.caption(f"{len(df_show):,} linhas exibidas.")

    # ── Exportação ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Exportar Resultados")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    c_xlsx, c_csv, _ = st.columns([1, 1, 2])

    with c_xlsx:
        with st.spinner("Gerando Excel..."):
            xlsx_bytes = eng.to_excel_bytes(df_res, s)
        st.download_button(
            label="📥 Baixar Excel (.xlsx)",
            data=xlsx_bytes,
            file_name=f"fidc_resultado_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c_csv:
        csv_bytes = eng.to_csv_bytes(df_res)
        st.download_button(
            label="📥 Baixar CSV (;)",
            data=csv_bytes,
            file_name=f"fidc_resultado_{ts}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption(
        "Excel: 3 abas (Resultado, Resumo Aging, Resumo Empresa) · "
        "CSV: separador `;`, BOM UTF-8, formato pt-BR."
    )
