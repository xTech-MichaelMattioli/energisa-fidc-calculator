"""
Módulo específico para cálculo de valor justo de distribuidoras padrão (não-VOLTZ)
Este módulo contém toda a lógica específica para distribuidoras tradicionais
que precisam do cálculo completo de valor justo após a correção monetária base.
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import time

class CalculadorValorJusto:
    """Classe auxiliar para estatísticas do DI-PRE"""
    
    def obter_estatisticas_di_pre(self, df_di_pre):
        """Obtém estatísticas do DataFrame DI-PRE"""
        if df_di_pre is None or df_di_pre.empty:
            return {}
        
        return {
            'total_registros': len(df_di_pre),
            'prazo_min': df_di_pre['meses_futuros'].min(),
            'prazo_max': df_di_pre['meses_futuros'].max(),
            'taxa_media': df_di_pre['252'].mean(),
            'taxa_min': df_di_pre['252'].min(),
            'taxa_max': df_di_pre['252'].max()
        }

class CalculadorValorJustoDistribuidoras:
    """
    Classe responsável pelo cálculo completo de valor justo para distribuidoras padrão
    (todas exceto VOLTZ, que tem seu próprio fluxo otimizado)
    """
    
    def __init__(self, params):
        self.params = params

    @staticmethod
    def _somar_meses_calendario(data_base: pd.Series, meses: pd.Series) -> pd.Series:
        """
        Soma meses respeitando calendário real (dias do mês e ano bissexto).

        Exemplo: 31/01 + 1 mês -> 28/02 (ou 29/02 em ano bissexto).
        """
        data_base_dt = pd.to_datetime(data_base, errors='coerce').fillna(pd.Timestamp(datetime.now()))
        meses_int = pd.to_numeric(meses, errors='coerce').fillna(0).astype(int)

        ano_base = data_base_dt.dt.year.to_numpy(dtype=np.int32)
        mes_base = data_base_dt.dt.month.to_numpy(dtype=np.int32)
        dia_base = data_base_dt.dt.day.to_numpy(dtype=np.int32)

        mes_total = (mes_base - 1) + meses_int.to_numpy(dtype=np.int32)
        ano_destino = ano_base + np.floor_divide(mes_total, 12)
        mes_destino = np.mod(mes_total, 12) + 1

        primeiro_dia_destino = pd.to_datetime(
            {
                'year': ano_destino,
                'month': mes_destino,
                'day': np.ones(len(mes_destino), dtype=np.int32),
            },
            errors='coerce',
        )
        ultimo_dia_destino = primeiro_dia_destino + pd.offsets.MonthEnd(0)
        dia_limite = ultimo_dia_destino.dt.day.to_numpy(dtype=np.int32)

        dia_destino = np.minimum(dia_base, dia_limite)

        return pd.to_datetime(
            {
                'year': ano_destino,
                'month': mes_destino,
                'day': dia_destino,
            },
            errors='coerce',
        )

    @staticmethod
    def _potencia_composta_estavel(base_taxa: pd.Series, expoente: pd.Series) -> np.ndarray:
        """Calcula (1 + taxa)^expoente com estabilidade numérica e alta precisão intermediária."""
        taxa = pd.to_numeric(base_taxa, errors='coerce').fillna(0.0).to_numpy(dtype=np.longdouble)
        expn = pd.to_numeric(expoente, errors='coerce').fillna(0.0).to_numpy(dtype=np.longdouble)

        # Evitar log1p inválido em taxas <= -100%
        taxa = np.maximum(taxa, np.longdouble(-0.999999999999999))
        fator = np.exp(np.log1p(taxa) * expn)

        # Limpeza para valores não finitos
        fator = np.where(np.isfinite(fator), fator, np.longdouble(0.0))
        return fator.astype(np.float64)
    
    def processar_valor_justo_distribuidoras(self, df_final_temp, log_container, progress_main):
        """
        Processa o cálculo completo de valor justo para distribuidoras padrão
        
        Args:
            df_final_temp: DataFrame com dados básicos já processados
            log_container: Container do Streamlit para logs
            progress_main: Barra de progresso principal
            
        Returns:
            DataFrame com valor justo calculado
        """
        
        try:
            # ============= PREPARAR DADOS BASE (ULTRA-RÁPIDO) =============
            # Garantir que data_base seja datetime
            if 'data_base' not in df_final_temp.columns:
                df_final_temp['data_base'] = datetime.now()
            df_final_temp['data_base'] = pd.to_datetime(df_final_temp['data_base'], errors='coerce')
            
            progress_main.progress(0.82)

            progress_main.progress(0.85)
            
            # ============= CÁLCULO DO PERÍODO ATÉ RECEBIMENTO (MERGE OTIMIZADO) =============
            with log_container:
                st.info("📊 **Merge dinâmico** de prazos de recebimento...")
            
            df_final_temp = self._calcular_meses_recebimento(df_final_temp, log_container)
            
            # ============= MERGE OTIMIZADO COM TAXAS DI-PRE (VETORIZADO) =============
            with log_container:
                st.info("📊 **Merge vetorizado** com taxas DI-PRE por prazo...")
            
            df_final_temp = self._aplicar_taxas_di_pre(df_final_temp, log_container)
            
            # ============= CÁLCULO DA TAXA DI-PRE ANUALIZADA (VETORIZADO) =============
            df_final_temp = self._calcular_taxas_anualizadas(df_final_temp)
            
            # ============= CÁLCULO DO IPCA MENSAL REAL DOS DADOS DO EXCEL =============
            df_final_temp = self._calcular_ipca_mensal(df_final_temp, log_container)
            
            # ============= CÁLCULO FINAL DO VALOR JUSTO =============
            progress_main.progress(0.88)
            
            with log_container:
                st.info("💰 **Calculando Valor Justo** conforme orientação do Thiago...")
            
            df_final_temp = self._calcular_valor_justo_final(df_final_temp, log_container)
            
            progress_main.progress(0.92)
            
            return df_final_temp
            
        except Exception as e:
            st.error(f"❌ Erro no cálculo do valor justo para distribuidoras: {str(e)}")
            raise e
    
    def _calcular_meses_recebimento(self, df_final_temp, log_container):
        """Calcula os meses até recebimento baseado na taxa de recuperação"""
        
        try:
            # Verificar se temos dados de taxa de recuperação carregados
            if 'df_taxa_recuperacao' in st.session_state and not st.session_state.df_taxa_recuperacao.empty:
                df_taxa = st.session_state.df_taxa_recuperacao.copy()

                registros_antes_merge = len(df_final_temp)

                # Normalizar chaves para merge e deduplicar a tabela de taxa para evitar many-to-many.
                df_final_temp['_empresa_merge'] = df_final_temp['empresa'].astype(str).str.strip()
                df_final_temp['_tipo_merge'] = df_final_temp['tipo'].astype(str).str.strip()
                df_final_temp['_aging_merge'] = df_final_temp['aging_taxa'].astype(str).str.strip()

                df_taxa_merge = df_taxa[['Empresa', 'Tipo', 'Aging', 'Prazo de recebimento']].copy()
                df_taxa_merge['Empresa'] = df_taxa_merge['Empresa'].astype(str).str.strip()
                df_taxa_merge['Tipo'] = df_taxa_merge['Tipo'].astype(str).str.strip()
                df_taxa_merge['Aging'] = df_taxa_merge['Aging'].astype(str).str.strip()

                duplicatas_taxa = int(df_taxa_merge.duplicated(subset=['Empresa', 'Tipo', 'Aging']).sum())
                if duplicatas_taxa > 0:
                    with log_container:
                        st.warning(
                            f"⚠️ {duplicatas_taxa:,} chave(s) duplicada(s) em taxa de recuperação "
                            "(Empresa/Tipo/Aging). Usando apenas a primeira ocorrência por chave."
                        )
                    df_taxa_merge = df_taxa_merge.drop_duplicates(
                        subset=['Empresa', 'Tipo', 'Aging'],
                        keep='first'
                    )
                
                # Fazer merge para pegar o prazo_recebimento baseado em empresa, tipo e aging
                df_final_temp = df_final_temp.merge(
                    df_taxa_merge,
                    left_on=['_empresa_merge', '_tipo_merge', '_aging_merge'],
                    right_on=['Empresa', 'Tipo', 'Aging'],
                    how='left',
                    validate='m:1'
                )

                if len(df_final_temp) != registros_antes_merge:
                    with log_container:
                        st.warning(
                            f"⚠️ Merge de prazo alterou contagem de linhas "
                            f"({registros_antes_merge:,} → {len(df_final_temp):,})."
                        )
                
                # Usar prazo_recebimento do merge, com fallback para valor padrão
                df_final_temp['meses_ate_recebimento'] = df_final_temp['Prazo de recebimento'].fillna(6).astype(int)
                
                # Limpar colunas auxiliares do merge
                colunas_merge = ['Empresa', 'Tipo', 'Aging', 'Prazo de recebimento', '_empresa_merge', '_tipo_merge', '_aging_merge']
                df_final_temp = df_final_temp.drop(columns=[col for col in colunas_merge if col in df_final_temp.columns])
                
                # Mostrar estatísticas do mapeamento
                contagem_meses = df_final_temp['meses_ate_recebimento'].value_counts().sort_index()
                
                with log_container:
                    st.success(f"✅ **Meses de recebimento** obtidos dinamicamente!")
                
                # Mostrar distribuição em um formato mais compacto
                distribuicao_str = ", ".join([f"{meses}m: {count:,}" for meses, count in contagem_meses.items()])
                with log_container:
                    st.info(f"📊 **Distribuição:** {distribuicao_str}")
            else:
                raise Exception("Dados de taxa de recuperação não encontrados no session_state")
                        
        except Exception as e:
            with log_container:
                st.warning(f"⚠️ Erro ao usar dados da taxa de recuperação: {str(e)}")
                st.info("📊 Usando valores padrão para meses de recebimento...")

            # Fallback padrão: 6 meses
            df_final_temp['meses_ate_recebimento'] = 6
        
        return df_final_temp
    
    def _aplicar_taxas_di_pre(self, df_final_temp, log_container):
        """Aplica as taxas DI-PRE baseadas no prazo de recebimento"""
        
        # Verificar se temos dados DI-PRE disponíveis
        if 'df_di_pre' in st.session_state and not st.session_state.df_di_pre.empty:
            df_di_pre = st.session_state.df_di_pre.copy()
            
            # Preparar dados DI-PRE para merge
            df_di_pre_merge = df_di_pre[['meses_futuros', '252']].copy()
            df_di_pre_merge.rename(columns={
                'meses_futuros': 'meses_ate_recebimento',
                '252': 'taxa_di_pre_percentual'
            }, inplace=True)

            df_di_pre_merge['meses_ate_recebimento'] = pd.to_numeric(
                df_di_pre_merge['meses_ate_recebimento'],
                errors='coerce'
            ).round().astype('Int64')
            df_di_pre_merge['taxa_di_pre_percentual'] = pd.to_numeric(
                df_di_pre_merge['taxa_di_pre_percentual'],
                errors='coerce'
            )
            df_di_pre_merge = df_di_pre_merge.dropna(subset=['meses_ate_recebimento', 'taxa_di_pre_percentual']).copy()
            df_di_pre_merge['meses_ate_recebimento'] = df_di_pre_merge['meses_ate_recebimento'].astype(int)

            duplicatas_di = int(df_di_pre_merge.duplicated(subset=['meses_ate_recebimento']).sum())
            if duplicatas_di > 0:
                with log_container:
                    st.warning(
                        f"⚠️ {duplicatas_di:,} prazo(s) duplicado(s) em DI-PRE. "
                        "Mantendo a primeira taxa por prazo para evitar duplicação de linhas."
                    )
                df_di_pre_merge = df_di_pre_merge.drop_duplicates(
                    subset=['meses_ate_recebimento'],
                    keep='first'
                )
            
            # Merge direto usando meses_ate_recebimento (ULTRA-RÁPIDO)
            registros_antes_merge = len(df_final_temp)
            df_final_temp = df_final_temp.merge(
                df_di_pre_merge,
                on='meses_ate_recebimento',
                how='left',
                validate='m:1'
            )

            if len(df_final_temp) != registros_antes_merge:
                with log_container:
                    st.warning(
                        f"⚠️ Merge DI-PRE alterou contagem de linhas "
                        f"({registros_antes_merge:,} → {len(df_final_temp):,})."
                    )
            
            # Para registros sem match exato, buscar o mais próximo
            mask_sem_taxa = df_final_temp['taxa_di_pre_percentual'].isna()
            registros_sem_taxa = mask_sem_taxa.sum()
            
            if registros_sem_taxa > 0:
                with log_container:
                    st.info(f"📊 **Buscando taxas mais próximas** para {registros_sem_taxa:,} registros...")

                prazos_disponiveis = df_di_pre_merge['meses_ate_recebimento'].to_numpy()
                taxas_disponiveis = df_di_pre_merge['taxa_di_pre_percentual'].to_numpy()

                prazos_sem_taxa = pd.to_numeric(
                    df_final_temp.loc[mask_sem_taxa, 'meses_ate_recebimento'],
                    errors='coerce'
                ).fillna(6).astype(int).to_numpy()

                idx_mais_proximo = np.abs(
                    prazos_sem_taxa[:, None] - prazos_disponiveis[None, :]
                ).argmin(axis=1)
                taxas_proximas = taxas_disponiveis[idx_mais_proximo]

                df_final_temp.loc[mask_sem_taxa, 'taxa_di_pre_percentual'] = taxas_proximas
            
            # Converter percentual para decimal
            df_final_temp['taxa_di_pre_decimal'] = df_final_temp['taxa_di_pre_percentual'] / 100
            
            # Estatísticas do merge
            registros_com_taxa = (~df_final_temp['taxa_di_pre_decimal'].isna()).sum()
            taxa_media = df_final_temp['taxa_di_pre_decimal'].mean() * 100
            
            with log_container:
                st.success(f"✅ **Merge DI-PRE concluído:** {registros_com_taxa:,}/{len(df_final_temp):,} registros com taxa (média: {taxa_media:.3f}%)")
        
        else:
            # Fallback para taxa padrão
            with log_container:
                st.warning("⚠️ Dados DI-PRE não disponíveis. Usando taxa padrão.")
            df_final_temp['taxa_di_pre_decimal'] = 0.10  # 10% ao ano como fallback
            df_final_temp['taxa_di_pre_percentual'] = 10.0
        
        return df_final_temp
    
    def _calcular_taxas_anualizadas(self, df_final_temp):
        """Calcula as taxas anualizadas com spread de risco"""
        
        # Aplicar spread de risco de 2.5% sobre a taxa DI-PRE
        spread_risco = 2.5  # 2.5%
        df_final_temp['taxa_di_pre_total_anual'] = (1 + df_final_temp['taxa_di_pre_decimal']) * (1 + spread_risco / 100) - 1

        # Converter taxa anual para mensal: (1 + taxa_anual)^(1/12) - 1
        df_final_temp['taxa_desconto_mensal'] = (1 + df_final_temp['taxa_di_pre_total_anual']) ** (1/12) - 1
            
        # Data estimada de recebimento por calendário real (sem aproximação de 30 dias)
        data_base = pd.to_datetime(df_final_temp.get('data_base'), errors='coerce').fillna(pd.Timestamp(datetime.now()))
        meses = pd.to_numeric(df_final_temp.get('meses_ate_recebimento'), errors='coerce').fillna(30).astype(int)

        df_final_temp['data_recebimento_estimada'] = self._somar_meses_calendario(
            data_base=data_base,
            meses=meses,
        )
        
        return df_final_temp
    
    def _calcular_ipca_mensal(self, df_final_temp, log_container):
        """Calcula o IPCA mensal baseado nos índices carregados"""
        
        st.info("📊 Calculando IPCA/IGPM com sazonalidade histórica (média móvel de 3 anos por mês)...")

        # Data base de referência da carteira (usa a data predominante; fallback para hoje)
        data_base_serie = pd.to_datetime(df_final_temp.get('data_base'), errors='coerce')
        data_base_validas = data_base_serie.dropna()
        if data_base_validas.empty:
            data_base_ref = pd.Timestamp(datetime.now())
        else:
            data_base_ref = pd.Timestamp(data_base_validas.mode().iloc[0])

        # ========== SELEÇÃO DOS ÍNDICES PARA CÁLCULO ==========
        if 'df_indices_economicos' in st.session_state:
            df_indices = st.session_state.df_indices_economicos.copy()
            tipo_calculo = "IGPM_IPCA (Distribuidoras)"
        elif 'df_indices_igpm' in st.session_state:
            df_indices = st.session_state.df_indices_igpm.copy()
            tipo_calculo = "IGPM (Fallback)"
        else:
            df_indices = pd.DataFrame()
            tipo_calculo = "Sem índices"

        st.info(f"📊 Usando {tipo_calculo} para projeção sazonal determinística")

        # Fallback padrão fixo (último recurso)
        ipca_mensal_fallback = 0.0037  # ~4.53% a.a.
        ipca_anual_fallback = (1 + ipca_mensal_fallback) ** 12 - 1

        if not df_indices.empty and {'data', 'indice'}.issubset(df_indices.columns):
            df_indices = df_indices.copy()
            df_indices['data'] = pd.to_datetime(df_indices['data'], errors='coerce')
            df_indices['indice'] = pd.to_numeric(df_indices['indice'], errors='coerce')
            df_indices = df_indices.dropna(subset=['data', 'indice']).sort_values('data').reset_index(drop=True)
        else:
            df_indices = pd.DataFrame(columns=['data', 'indice'])

        if not df_indices.empty:
            # Regra: se não existir índice da data base atual, usa o último disponível até a data base.
            # Se não houver nenhum até a data base, usa o último da série.
            df_ate_data_base = df_indices[df_indices['data'] <= data_base_ref]
            usou_fallback_data_base = False

            if not df_ate_data_base.empty:
                linha_ref = df_ate_data_base.iloc[-1]
                data_ref = pd.Timestamp(linha_ref['data'])
                indice_atual_num = float(linha_ref['indice'])
                if data_ref.to_period('M') != data_base_ref.to_period('M'):
                    usou_fallback_data_base = True
            else:
                linha_ref = df_indices.iloc[-1]
                data_ref = pd.Timestamp(linha_ref['data'])
                indice_atual_num = float(linha_ref['indice'])
                usou_fallback_data_base = True

            if usou_fallback_data_base:
                st.warning(
                    "⚠️ Índice da competência da data base não encontrado. "
                    f"Usando último índice disponível em {data_ref.strftime('%Y-%m')} "
                    "como referência para a projeção."
                )

            # Série mensal consolidada (último índice de cada mês)
            df_mensal = (
                df_indices
                .assign(periodo=df_indices['data'].dt.to_period('M'))
                .sort_values('data')
                .groupby('periodo', as_index=False)
                .agg(data=('data', 'max'), indice=('indice', 'last'))
                .sort_values('data')
                .reset_index(drop=True)
            )
            df_mensal['taxa_mensal'] = df_mensal['indice'].pct_change()

            # Histórico elegível para sazonalidade: até a data de referência
            df_taxas_hist = df_mensal[
                (df_mensal['data'] <= data_ref) & df_mensal['taxa_mensal'].notna()
            ].copy()
            df_taxas_hist['mes'] = df_taxas_hist['data'].dt.month

            # Taxa global de segurança: média dos últimos 12 meses válidos
            if not df_taxas_hist.empty:
                taxa_global = float(df_taxas_hist['taxa_mensal'].tail(12).mean())
            else:
                taxa_global = float(ipca_mensal_fallback)

            if pd.isna(taxa_global):
                taxa_global = float(ipca_mensal_fallback)

            # Regra 2 (sazonalidade): para cada mês futuro, usa média dos mesmos meses
            # dos últimos 3 anos observados (até 3 observações por mês).
            mapa_taxa_mes = {}
            for mes in range(1, 13):
                taxas_mes = df_taxas_hist.loc[df_taxas_hist['mes'] == mes, 'taxa_mensal'].tail(3)
                if not taxas_mes.empty:
                    mapa_taxa_mes[mes] = float(taxas_mes.mean())
                else:
                    mapa_taxa_mes[mes] = float(taxa_global)

            periodo_ref = data_ref.to_period('M')
            taxas_projetadas_12 = []
            for passo in range(1, 13):
                periodo_futuro = periodo_ref + passo
                taxa_mes = mapa_taxa_mes.get(periodo_futuro.month, taxa_global)
                taxas_projetadas_12.append(float(taxa_mes))

            taxas_projetadas_arr = np.array(taxas_projetadas_12, dtype=float)

            # IPCA mensal reportado = primeira taxa projetada (mês imediatamente após referência)
            ipca_mensal_calculado = float(taxas_projetadas_arr[0]) if len(taxas_projetadas_arr) > 0 else float(taxa_global)

            # IPCA anual reportado = composição das próximas 12 taxas projetadas
            if len(taxas_projetadas_arr) > 0:
                ipca_anual = float(np.prod(1.0 + taxas_projetadas_arr) - 1.0)
            else:
                ipca_anual = float((1.0 + ipca_mensal_calculado) ** 12 - 1.0)

            df_final_temp['ipca_anual'] = float(ipca_anual)
            df_final_temp['ipca_mensal'] = float(ipca_mensal_calculado)

            st.success(f"""
            ✅ **IPCA sazonal calculado com histórico real!**
            📅 Data base de referência: {data_base_ref.strftime('%Y-%m')}
            📊 Índice de referência: {indice_atual_num:.6f} ({data_ref.strftime('%Y-%m')})
            📈 IPCA Anual Projetado (12m): {ipca_anual*100:.2f}%
            🔢 IPCA Mensal Projetado (m+1): {ipca_mensal_calculado*100:.4f}%
            """)
        else:
            df_final_temp['ipca_anual'] = float(ipca_anual_fallback)
            df_final_temp['ipca_mensal'] = float(ipca_mensal_fallback)

            st.warning(
                "⚠️ Não foi possível usar histórico de índices para sazonalidade. "
                f"Aplicando fallback fixo: IPCA mensal={ipca_mensal_fallback:.6f} "
                f"(IPCA anual implícito={ipca_anual_fallback*100:.2f}%)."
            )

        # Esses campos foram descontinuados e não devem seguir no output final.
        colunas_descontinuadas = ['indice_atual', 'indice_12m']
        colunas_presentes = [col for col in colunas_descontinuadas if col in df_final_temp.columns]
        if colunas_presentes:
            df_final_temp = df_final_temp.drop(columns=colunas_presentes)

        # Mantém a fórmula original do fator de correção até recebimento.
        meses_recebimento_num = pd.to_numeric(
            df_final_temp.get('meses_ate_recebimento'), errors='coerce'
        ).fillna(0).clip(lower=0)
        df_final_temp['fator_correcao_ate_recebimento'] = (1 + df_final_temp['ipca_mensal']) ** meses_recebimento_num

        # Calcular mora simples de 1% a.m. até o recebimento
        valor_corrigido_base = pd.to_numeric(df_final_temp.get('valor_corrigido'), errors='coerce').fillna(0.0)
        fator_correcao_receb = pd.to_numeric(df_final_temp.get('fator_correcao_ate_recebimento'), errors='coerce').fillna(1.0)
        df_final_temp['mora_ate_recebimento'] = (valor_corrigido_base * 0.01 * meses_recebimento_num).clip(lower=0)

        # Calcular valor corrigido até recebimento com correção monetária + mora até o recebimento
        df_final_temp['valor_corrigido_ate_recebimento'] = (
            valor_corrigido_base * fator_correcao_receb
            + df_final_temp['mora_ate_recebimento']
        )

        # Garantir posição das colunas logo após o fator de correção
        col_mora_receb = 'mora_ate_recebimento'
        col_valor_receb = 'valor_corrigido_ate_recebimento'
        col_fator_receb = 'fator_correcao_ate_recebimento'
        if (
            col_fator_receb in df_final_temp.columns
            and col_mora_receb in df_final_temp.columns
            and col_valor_receb in df_final_temp.columns
        ):
            colunas_ordenadas = [
                col for col in df_final_temp.columns
                if col not in {col_mora_receb, col_valor_receb}
            ]
            idx_fator = colunas_ordenadas.index(col_fator_receb) + 1
            colunas_ordenadas.insert(idx_fator, col_mora_receb)
            colunas_ordenadas.insert(idx_fator + 1, col_valor_receb)
            df_final_temp = df_final_temp[colunas_ordenadas]

        # Aplicar taxa de desconto
        df_final_temp['fator_de_desconto'] = self._potencia_composta_estavel(
            df_final_temp.get('taxa_desconto_mensal', 0),
            df_final_temp.get('meses_ate_recebimento', 0),
        )
        
        # Calcular multa por atraso
        data_atual = datetime.now()
        df_final_temp['dias_atraso'] = (data_atual - df_final_temp['data_recebimento_estimada']).dt.days.clip(lower=0)
        
        # Multa por atraso: 1% ao mês = 0.01/30 por dia
        taxa_multa_diaria = 0.01 / 30
        df_final_temp['multa_atraso'] = df_final_temp['dias_atraso'] * taxa_multa_diaria
        
        # Aplicar multa mínima de 6% mesmo sem atraso (margem de segurança)
        multa_minima = 0.06
        df_final_temp['multa_final'] = df_final_temp['multa_atraso'].clip(lower=multa_minima)
        
        return df_final_temp
    
    def _calcular_valor_justo_final(self, df_final_temp, log_container):
        """Calcula valor recuperável até recebimento e prepara fator de desconto.
        
        A sequência final de cálculo do valor justo continua em
        `calcular_valor_justo_reajustado` (calculador_correcao.py).
        """
        
        # ===== PASSO 1: VALOR RECUPERÁVEL ATÉ RECEBIMENTO =====
        valor_corrigido_recebimento = pd.to_numeric(
            df_final_temp.get('valor_corrigido_ate_recebimento', 0),
            errors='coerce'
        ).fillna(0.0)

        if 'taxa_recuperacao' in df_final_temp.columns:
            taxa_recuperacao = pd.to_numeric(df_final_temp['taxa_recuperacao'], errors='coerce').fillna(0.0)
            df_final_temp['valor_recuperavel_ate_recebimento'] = (valor_corrigido_recebimento * taxa_recuperacao).clip(lower=0)
        else:
            df_final_temp['valor_recuperavel_ate_recebimento'] = 0.0

        # ===== PASSO 2: TAXAS CDI + SPREAD =====
        with log_container:
            st.info("📊 **Usando taxas CDI** já calculadas no merge vetorizado...")

        df_final_temp['cdi_taxa_prazo'] = df_final_temp['taxa_di_pre_decimal']

        spread_risco = 0.025  # 2.5% a.a.
        df_final_temp['taxa_desconto_total'] = (
            (1 + df_final_temp['cdi_taxa_prazo']) * (1 + spread_risco)
        ) - 1

        # ===== PASSO 3: FATOR DE DESCONTO (base 360 dias) =====
        data_base_dt = pd.to_datetime(df_final_temp['data_base'], errors='coerce').fillna(pd.Timestamp(datetime.now()))
        meses_rec = pd.to_numeric(df_final_temp['meses_ate_recebimento'], errors='coerce').fillna(0)
        df_final_temp['dias_ate_recebimento'] = meses_rec * 30
        df_final_temp['data_ate_recebimento'] = data_base_dt + pd.to_timedelta(df_final_temp['dias_ate_recebimento'], unit='D')
        df_final_temp['fator_de_desconto_vp'] = self._potencia_composta_estavel(
            df_final_temp.get('taxa_desconto_total', 0),
            df_final_temp['dias_ate_recebimento'] / 360,
        )

        # ===== ESTATÍSTICAS =====
        with log_container:
            valor_total_recuperavel = df_final_temp['valor_recuperavel_ate_recebimento'].sum()
            st.success(f"""
            ✅ **Valor Recuperável até Recebimento calculado!**
            💰 Total Recuperável: R$ {valor_total_recuperavel:,.2f}
            
            🔢 Próxima etapa: aplicar remuneração variável e trazer a valor presente.
            """)

        # ===== COLUNA DE CONTROLE =====
        df_final_temp['data_calculo'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return df_final_temp
