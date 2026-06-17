"""
Mapeador de campos para estrutura padronizada
Baseado no notebook original
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Dict, List
import streamlit as st


class MapeadorCampos:
    """
    Classe para mapear campos das bases para estrutura padronizada.
    """
    
    def __init__(self, params):
        self.params = params
        # Importar calculador VOLTZ para detecção
        from .calculador_voltz import CalculadorVoltz
        self.calculador_voltz = CalculadorVoltz(params)
    
    def identificar_tipo_distribuidora(self, nome_arquivo: str) -> str:
        """
        Identifica se é VOLTZ ou distribuidora padrão.
        """
        if self.calculador_voltz.identificar_voltz(nome_arquivo):
            return "VOLTZ"
        else:
            return "PADRAO"
    
    def criar_mapeamento_automatico(self, df: pd.DataFrame, nome_distribuidora: str) -> Dict[str, str]:
        """
        Cria mapeamento automático baseado em análise dos nomes das colunas.
        """
        if df.empty:
            return {}
        
        st.subheader(f"🗺️ Mapeamento Automático")
        
        mapeamento = {}
        
        # Buscar automaticamente por padrões
        for col in df.columns:
            if not isinstance(col, str):
                continue
            col_lower = col.lower()

            # Empresa
            if any(termo in col_lower for termo in ['empresa']) and 'empresa' not in mapeamento:
                mapeamento['empresa'] = col
            
            # Tipo
            elif any(termo in col_lower for termo in ['tipo']) and 'tipo' not in mapeamento:
                mapeamento['tipo'] = col
            
            # Status
            elif any(termo in col_lower for termo in ['status']) and 'status' not in mapeamento:
                mapeamento['status'] = col
            
            # Situação
            elif any(termo in col_lower for termo in ['situacao', 'situação', 'situaçao', 'situacão']) and 'situacao' not in mapeamento:
                mapeamento['situacao'] = col
            
            # Cliente/Nome
            if any(termo in col_lower for termo in ['cliente', 'nome']) and 'nome_cliente' not in mapeamento:
                mapeamento['nome_cliente'] = col
            
            # Documento
            elif any(termo in col_lower for termo in ['cpf', 'cnpj', 'documento']) and 'documento' not in mapeamento:
                mapeamento['documento'] = col

            # Classe
            elif any(termo in col_lower for termo in ['classe', 'categoria']) and 'classe' not in mapeamento:
                mapeamento['classe'] = col
            
            # Contrato/UC
            elif any(termo in col_lower for termo in ['contrato', 'uc', 'instalacao', 'conta', 'vinculado']) and 'contrato' not in mapeamento:
                mapeamento['contrato'] = col
            
            # Valor principal
            elif (
                any(termo in col_lower for termo in ['fatura', 'faturas', 'valor principal', 'principal', 'valor cedido'])
                and not any(termo in col_lower for termo in ['nao cedido', 'não cedido', 'n cedido', 'nao_cedido', 'não_cedido'])
                and 'valor_principal' not in mapeamento
            ):
                mapeamento['valor_principal'] = col

            # Valor não cedido
            elif (
                any(termo in col_lower for termo in ['nao cedido', 'não cedido', 'n cedido', 'nao_cedido', 'não_cedido'])
                and 'valor_nao_cedido' not in mapeamento
            ):
                mapeamento['valor_nao_cedido'] = col

            # Valor Terceiro
            elif any(termo in col_lower for termo in ['terceiro', 'terceiros']) and 'valor_terceiro' not in mapeamento:
                mapeamento['valor_terceiro'] = col

            # Valor CIP
            elif any(termo in col_lower for termo in ['cip', 'cips']) and 'valor_cip' not in mapeamento:
                mapeamento['valor_cip'] = col
            
            # Data de vencimento
            elif any(termo in col_lower for termo in ['vencimento', 'venc', 'prazo']) and 'data_vencimento' not in mapeamento:
                mapeamento['data_vencimento'] = col
        
        st.info("🔗 **Nota**: id_padronizado será criado automaticamente baseado em Nome do Cliente + Data de Vencimento")
        
        return mapeamento
    
    def permitir_mapeamento_manual(self, df: pd.DataFrame, mapeamento_auto: Dict[str, str], nome_arquivo: str, key_suffix: str = "") -> Dict[str, str]:
        """
        Permite ajuste manual do mapeamento via interface Streamlit.
        Para VOLTZ, alguns campos são preenchidos automaticamente.
        """
        
        # Detectar tipo de distribuidora
        tipo_distribuidora = self.identificar_tipo_distribuidora(nome_arquivo)
        
        # Campos padrão que precisamos mapear
        if tipo_distribuidora == "VOLTZ":
            # Para VOLTZ: apenas campos essenciais (sem classe, situacao, tipo)
            campos_padrao = [
                'nome_cliente', 'documento', 'contrato',
                'valor_principal', 'data_vencimento'
            ]
        else:
            # Para outras distribuidoras: todos os campos
            campos_padrao = [
                'nome_cliente', 'documento', 'contrato', 'classe', 'situacao',
                'valor_principal', 'valor_nao_cedido', 'valor_terceiro', 'valor_cip',
                'data_vencimento', 'empresa', 'tipo', 'status'
            ]
        
        # Para VOLTZ, remover campos que são preenchidos automaticamente
        if tipo_distribuidora == "VOLTZ":
            st.success("⚡ **VOLTZ detectada!** Campos específicos serão preenchidos automaticamente:")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("✅ **empresa** → 'VOLTZ'")
                st.write("✅ **valor_nao_cedido** → 0")
            with col2:
                st.write("✅ **valor_terceiro** → 0") 
                st.write("✅ **valor_cip** → 0")
            
            # Campos automáticos já não estão na lista para VOLTZ
        
        mapeamento_final = {}
        
        # Para VOLTZ, adicionar campos automáticos
        if tipo_distribuidora == "VOLTZ":
            mapeamento_final['empresa'] = None  # Será preenchido automaticamente
            mapeamento_final['valor_nao_cedido'] = None  # Será preenchido como 0
            mapeamento_final['valor_terceiro'] = None   # Será preenchido como 0
            mapeamento_final['valor_cip'] = None        # Será preenchido como 0
        
        # Criar selectbox para cada campo padrão
        colunas_disponiveis = ['[Não mapear]'] + list(df.columns)
        
        st.markdown("---")
        st.subheader("🗺️ Mapeamento Manual de Campos")
        
        col1, col2 = st.columns(2)
        
        for i, campo in enumerate(campos_padrao):
            # Valor padrão do mapeamento automático
            valor_padrao = mapeamento_auto.get(campo, '[Não mapear]')
            if valor_padrao not in colunas_disponiveis:
                valor_padrao = '[Não mapear]'
            
            # Determinar em qual coluna colocar
            container = col1 if i % 2 == 0 else col2
            
            with container:
                # Verificar se campo não foi mapeado
                is_not_mapped = valor_padrao == '[Não mapear]'
                
                # Criar label com indicação visual (apenas emojis, sem fundo colorido)
                if is_not_mapped:
                    label = f"🔴 **{campo.replace('_', ' ').title()}** ⚠️"
                    help_text = "⚠️ Campo obrigatório não encontrado automaticamente - selecione a coluna correspondente"
                else:
                    label = f"✅ **{campo.replace('_', ' ').title()}**"
                    help_text = f"Mapeado automaticamente para: {valor_padrao}"
                
                coluna_selecionada = st.selectbox(
                    label,
                    options=colunas_disponiveis,
                    index=colunas_disponiveis.index(valor_padrao),
                    key=f"map_{campo}{key_suffix}",
                    help=help_text
                )
                
                if coluna_selecionada != '[Não mapear]':
                    mapeamento_final[campo] = coluna_selecionada
        
        # Resumo do mapeamento
        st.markdown("---")
        campos_mapeados = len([v for v in mapeamento_final.values() if v is not None])
        campos_automaticos = len([v for v in mapeamento_final.values() if v is None])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Campos Mapeados", campos_mapeados)
        with col2:
            st.metric("⚡ Campos Automáticos", campos_automaticos)
        with col3:
            st.metric("📊 Total", campos_mapeados + campos_automaticos)
        
        return mapeamento_final
    
    def aplicar_mapeamento(self, df: pd.DataFrame, mapeamento: Dict[str, str], nome_distribuidora: str) -> pd.DataFrame:
        """
        Aplica mapeamento criando DataFrame padronizado.
        Para VOLTZ, adiciona automaticamente campos específicos.
        """
        if df.empty or not mapeamento:
            return pd.DataFrame()
        
        st.subheader(f"🔄 Aplicando Mapeamento - {nome_distribuidora}")
        
        # Detectar tipo de distribuidora
        tipo_distribuidora = self.identificar_tipo_distribuidora(nome_distribuidora)
        
        df_padronizado = pd.DataFrame()
        
        # Aplicar mapeamentos disponíveis
        campos_mapeados = 0
        for campo_padrao, campo_original in mapeamento.items():
            if campo_original is not None and campo_original in df.columns:
                df_padronizado[campo_padrao] = df[campo_original]
                campos_mapeados += 1
            elif campo_original is not None:
                st.warning(f"⚠️ Campo {campo_original} não encontrado")
        
        # Para VOLTZ, adicionar campos automáticos
        if tipo_distribuidora == "VOLTZ":
            df_padronizado['empresa'] = "VOLTZ"
            df_padronizado['valor_nao_cedido'] = 0
            df_padronizado['valor_terceiro'] = 0
            df_padronizado['valor_cip'] = 0
            campos_mapeados += 4
            
            st.success("⚡ Campos VOLTZ preenchidos automaticamente:")
        
        if campos_mapeados > 0:
            # Criar ID padronizado único
            self.criar_id_padronizado(df_padronizado, df, nome_distribuidora)
            
            # Adicionar campos de controle
            df_padronizado['base_origem'] = nome_distribuidora
            df_padronizado['data_base'] = self.params.data_base_padrao  # Usar data padrão
            
            st.success(f"✅ DataFrame padronizado criado: {len(df_padronizado)} registros x {len(df_padronizado.columns)} colunas")
        else:
            st.error("❌ Nenhum campo foi mapeado com sucesso")
        
        return df_padronizado
    
    def criar_id_padronizado(self, df_padronizado: pd.DataFrame, df_original: pd.DataFrame, nome_distribuidora: str):
        """
        Cria ID padronizado único baseado na combinação Nome + Data Vencimento.
        """
        # Identificar campos de nome e data de vencimento
        campo_nome = None
        campo_data_venc = None
        
        # Procurar campo de nome
        if 'nome_cliente' in df_padronizado.columns:
            campo_nome = 'nome_cliente'
        else:
            for col in df_original.columns:
                if isinstance(col, str):
                    col_lower = col.lower()
                    if any(termo in col_lower for termo in ['nome', 'cliente', 'razao']) and campo_nome is None:
                        campo_nome = col
                        break
        
        # Procurar campo de data de vencimento
        if 'data_vencimento' in df_padronizado.columns:
            campo_data_venc = 'data_vencimento'
        else:
            for col in df_original.columns:
                if isinstance(col, str):
                    col_lower = col.lower()
                    if any(termo in col_lower for termo in ['vencimento', 'venc', 'prazo', 'data']) and campo_data_venc is None:
                        campo_data_venc = col
                        break
        
        if campo_nome and campo_data_venc:
            st.info(f"🔗 Criando IDs únicos baseados em: **{campo_nome}** + **{campo_data_venc}**")
            
            # Criar ID único combinando nome + data
            def criar_id_unico(row):
                try:
                    # Buscar nome no df_padronizado ou df_original
                    if campo_nome in df_padronizado.columns:
                        nome = str(row[campo_nome]).strip() if pd.notna(row[campo_nome]) else "SEM_NOME"
                    else:
                        idx = row.name
                        nome = str(df_original.loc[idx, campo_nome]).strip() if pd.notna(df_original.loc[idx, campo_nome]) else "SEM_NOME"
                    
                    # Buscar data no df_padronizado ou df_original
                    if campo_data_venc in df_padronizado.columns:
                        data_venc = row[campo_data_venc]
                    else:
                        idx = row.name
                        data_venc = df_original.loc[idx, campo_data_venc]
                    
                    # Limpar nome (remover caracteres especiais)
                    nome_limpo = re.sub(r'[^A-Za-z0-9\s]', '', nome)
                    nome_limpo = re.sub(r'\s+', '_', nome_limpo.strip().upper())
                    
                    # Converter data para string
                    if pd.notna(data_venc):
                        if isinstance(data_venc, str):
                            data_str = data_venc.replace('/', '').replace('-', '').replace(' ', '')[:8]
                        else:
                            try:
                                data_obj = pd.to_datetime(data_venc)
                                data_str = data_obj.strftime('%Y%m%d')
                            except:
                                data_str = "SEMDATA"
                    else:
                        data_str = "SEMDATA"
                    
                    # Criar ID único
                    id_unico = f"{nome_distribuidora}_{nome_limpo}_{data_str}"
                    
                    # Limitar tamanho se necessário
                    if len(id_unico) > 100:
                        nome_truncado = nome_limpo[:50]
                        id_unico = f"{nome_distribuidora}_{nome_truncado}_{data_str}"
                    
                    return id_unico
                    
                except Exception:
                    # Em caso de erro, criar ID baseado no índice
                    return f"{nome_distribuidora}_REG_{row.name}"
            
            # Aplicar função para criar IDs
            df_padronizado['id_padronizado'] = df_padronizado.apply(criar_id_unico, axis=1)
            
            # Verificar unicidade
            ids_unicos = df_padronizado['id_padronizado'].nunique()
            total_registros = len(df_padronizado)
            
            if ids_unicos < total_registros:
                st.warning(f"⚠️ Detectadas {total_registros - ids_unicos} duplicatas - adicionando sufixos...")
                # Adicionar sufixos para garantir unicidade
                df_padronizado['id_padronizado'] = df_padronizado.groupby('id_padronizado').cumcount().astype(str).replace('0', '') + '_' + df_padronizado['id_padronizado']
                df_padronizado['id_padronizado'] = df_padronizado['id_padronizado'].str.replace('^_', '', regex=True)
                
                st.success(f"✅ Unicidade garantida: {df_padronizado['id_padronizado'].nunique()} IDs únicos")
            else:
                st.success(f"✅ IDs únicos criados: {ids_unicos}/{total_registros}")
            
        else:
            st.warning("⚠️ Campos necessários para ID não encontrados - criando IDs sequenciais")
            # Criar ID simples baseado no índice
            df_padronizado['id_padronizado'] = [f"{nome_distribuidora}_REG_{i+1}" for i in range(len(df_padronizado))]
