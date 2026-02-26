"""
Gerenciador de Checkpoints de Dados
Responsável por detectar mudanças nos dados e evitar reprocessamento desnecessário
"""
import streamlit as st
import pandas as pd
import hashlib
import pickle
from typing import Any, Dict, Optional
from datetime import datetime


class CheckpointManager:
    """
    Classe responsável por gerenciar checkpoints de dados e detectar mudanças
    """
    
    def __init__(self):
        self.session_key_prefix = "checkpoint_"
    
    def _calcular_hash_dataframe(self, df: pd.DataFrame) -> str:
        """
        Calcula hash único de um DataFrame baseado em seu conteúdo
        """
        try:
            # Usar apenas colunas relevantes e valores não-nulos para o hash
            hash_data = []
            
            # Adicionar informações básicas do DataFrame
            hash_data.append(f"shape:{df.shape}")
            hash_data.append(f"columns:{sorted(df.columns.tolist())}")
            
            # Adicionar hash das primeiras e últimas linhas para detectar mudanças
            if not df.empty:
                # Hash das primeiras 5 linhas
                hash_data.append(f"head:{df.head().to_string()}")
                # Hash das últimas 5 linhas
                hash_data.append(f"tail:{df.tail().to_string()}")
                # Soma total de valores numéricos para detectar alterações
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    hash_data.append(f"sum:{df[numeric_cols].sum().sum()}")
            
            # Criar hash MD5
            hash_string = "|".join(str(item) for item in hash_data)
            return hashlib.md5(hash_string.encode()).hexdigest()
            
        except Exception as e:
            st.warning(f"⚠️ Erro ao calcular hash do DataFrame: {str(e)}")
            return str(datetime.now().timestamp())
    
    def _calcular_hash_parametros(self, **kwargs) -> str:
        """
        Calcula hash de parâmetros de entrada
        """
        try:
            # Converter parâmetros para string ordenada
            params_str = "|".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            return hashlib.md5(params_str.encode()).hexdigest()
        except Exception:
            return str(datetime.now().timestamp())
    
    def verificar_checkpoint(self, checkpoint_name: str, 
                           dataframes: Dict[str, pd.DataFrame] = None,
                           parametros: Dict[str, Any] = None) -> bool:
        """
        Verifica se existe um checkpoint válido para os dados fornecidos
        
        Args:
            checkpoint_name: Nome único do checkpoint
            dataframes: Dicionário com DataFrames a serem verificados
            parametros: Dicionário com parâmetros adicionais
            
        Returns:
            True se checkpoint é válido, False caso contrário
        """
        session_key = f"{self.session_key_prefix}{checkpoint_name}"
        
        # Verificar se checkpoint existe
        if session_key not in st.session_state:
            return False
        
        checkpoint_data = st.session_state[session_key]
        
        # Verificar hash dos DataFrames
        if dataframes:
            for df_name, df in dataframes.items():
                hash_atual = self._calcular_hash_dataframe(df)
                hash_salvo = checkpoint_data.get('df_hashes', {}).get(df_name)
                
                if hash_atual != hash_salvo:
                    return False
        
        # Verificar hash dos parâmetros
        if parametros:
            hash_params_atual = self._calcular_hash_parametros(**parametros)
            hash_params_salvo = checkpoint_data.get('params_hash')
            
            if hash_params_atual != hash_params_salvo:
                return False
        
        return True
    
    def salvar_checkpoint(self, checkpoint_name: str, 
                         resultado: Any,
                         dataframes: Dict[str, pd.DataFrame] = None,
                         parametros: Dict[str, Any] = None):
        """
        Salva um checkpoint com resultado e metadados
        
        Args:
            checkpoint_name: Nome único do checkpoint
            resultado: Resultado a ser salvo
            dataframes: Dicionário com DataFrames usados
            parametros: Dicionário com parâmetros usados
        """
        session_key = f"{self.session_key_prefix}{checkpoint_name}"
        
        checkpoint_data = {
            'resultado': resultado,
            'timestamp': datetime.now().isoformat(),
            'df_hashes': {},
            'params_hash': None
        }
        
        # Calcular hashes dos DataFrames
        if dataframes:
            for df_name, df in dataframes.items():
                checkpoint_data['df_hashes'][df_name] = self._calcular_hash_dataframe(df)
        
        # Calcular hash dos parâmetros
        if parametros:
            checkpoint_data['params_hash'] = self._calcular_hash_parametros(**parametros)
        
        # Salvar no session state
        st.session_state[session_key] = checkpoint_data
    
    def obter_resultado_checkpoint(self, checkpoint_name: str) -> Any:
        """
        Obtém o resultado salvo em um checkpoint
        
        Args:
            checkpoint_name: Nome do checkpoint
            
        Returns:
            Resultado salvo ou None se não existe
        """
        session_key = f"{self.session_key_prefix}{checkpoint_name}"
        
        if session_key in st.session_state:
            return st.session_state[session_key]['resultado']
        
        return None
    
    def limpar_checkpoint(self, checkpoint_name: str):
        """
        Remove um checkpoint específico
        """
        session_key = f"{self.session_key_prefix}{checkpoint_name}"
        
        if session_key in st.session_state:
            del st.session_state[session_key]
    
    def limpar_todos_checkpoints(self):
        """
        Remove todos os checkpoints
        """
        keys_para_remover = [key for key in st.session_state.keys() 
                           if key.startswith(self.session_key_prefix)]
        
        for key in keys_para_remover:
            del st.session_state[key]
    
    def listar_checkpoints(self) -> Dict[str, Dict]:
        """
        Lista todos os checkpoints ativos
        """
        checkpoints = {}
        
        for key, value in st.session_state.items():
            if key.startswith(self.session_key_prefix):
                checkpoint_name = key.replace(self.session_key_prefix, "")
                checkpoints[checkpoint_name] = {
                    'timestamp': value.get('timestamp'),
                    'dataframes': list(value.get('df_hashes', {}).keys()),
                    'tem_parametros': value.get('params_hash') is not None
                }
        
        return checkpoints
    
    def exibir_status_checkpoints(self):
        """
        Exibe status dos checkpoints na interface Streamlit
        """
        checkpoints = self.listar_checkpoints()
        
        if checkpoints:
            st.markdown("### 📋 Status dos Checkpoints")
            
            for nome, info in checkpoints.items():
                with st.expander(f"🔖 {nome} ({info['timestamp']})"):
                    st.write(f"**DataFrames:** {', '.join(info['dataframes']) if info['dataframes'] else 'Nenhum'}")
                    st.write(f"**Parâmetros:** {'Sim' if info['tem_parametros'] else 'Não'}")
                    
                    if st.button(f"🗑️ Limpar {nome}", key=f"limpar_{nome}"):
                        self.limpar_checkpoint(nome)
                        st.success(f"✅ Checkpoint '{nome}' removido!")
                        st.rerun()
            
            if st.button("🗑️ Limpar Todos os Checkpoints", key="limpar_todos_checkpoints"):
                self.limpar_todos_checkpoints()
                st.success("✅ Todos os checkpoints foram removidos!")
                st.rerun()
        else:
            st.info("ℹ️ Nenhum checkpoint ativo encontrado.")


# Instância global do gerenciador
checkpoint_manager = CheckpointManager()


def usar_checkpoint(checkpoint_name: str, 
                   funcao_processamento,
                   dataframes: Dict[str, pd.DataFrame] = None,
                   parametros: Dict[str, Any] = None,
                   mostrar_cache_hit: bool = True,
                   **kwargs_funcao):
    """
    Decorator/função helper para usar checkpoints automaticamente
    
    Args:
        checkpoint_name: Nome único do checkpoint
        funcao_processamento: Função que realiza o processamento
        dataframes: DataFrames a serem monitorados
        parametros: Parâmetros a serem monitorados
        mostrar_cache_hit: Se deve mostrar mensagem quando usa cache
        **kwargs_funcao: Argumentos para a função de processamento
        
    Returns:
        Resultado do processamento (do cache ou recém-calculado)
    """
    # Verificar se existe checkpoint válido
    if checkpoint_manager.verificar_checkpoint(checkpoint_name, dataframes, parametros):
        if mostrar_cache_hit:
            st.info(f"♻️ **Cache Hit**: Usando dados já processados para '{checkpoint_name}'")
        return checkpoint_manager.obter_resultado_checkpoint(checkpoint_name)
    
    # Processar dados se não há checkpoint válido
    with st.spinner(f"🔄 Processando '{checkpoint_name}'..."):
        resultado = funcao_processamento(**kwargs_funcao)
    
    # Salvar checkpoint
    checkpoint_manager.salvar_checkpoint(
        checkpoint_name, 
        resultado, 
        dataframes, 
        parametros
    )
    
    st.success(f"✅ Processamento de '{checkpoint_name}' concluído e salvo em cache!")
    
    return resultado
