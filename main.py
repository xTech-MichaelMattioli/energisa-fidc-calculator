"""
FIDC Calculator - Energisa
Aplicação Streamlit para Cálculo de Valor Corrigido
Sistema Principal de Navegação
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Adicionar pasta de páginas ao path
pages_path = Path(__file__).parent / "pages"
sys.path.append(str(pages_path))

# Configuração da página principal
st.set_page_config(
    page_title="FIDC Calculator - Energisa",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para identidade visual da Energisa
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #00A859 0%, #28C76F 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 8px rgba(0, 168, 89, 0.3);
    }
    
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #00A859;
        margin: 0.5rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .stProgress .st-bo {
        background: linear-gradient(90deg, #00A859 0%, #28C76F 100%);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>⚡ FIDC Calculator - Distribuidoras</h1>
        <h3>Sistema de Cálculo de Valor Justo</h3>
        <p><strong>Objetivo:</strong> Processar bases de distribuidoras até o cálculo do valor justo<br>
        <strong>Escopo:</strong> Carregamento → Mapeamento → Aging → Correção Monetária → Valor Justo</p>
        <p><em>Data: {}</em></p>
    </div>
    """.format(datetime.now().strftime('%d de %B de %Y')), unsafe_allow_html=True)
    
    # Inicializar estado da sessão se necessário
    from utils.parametros_correcao import ParametrosCorrecao
    
    if 'params' not in st.session_state:
        st.session_state.params = ParametrosCorrecao()
    
    # Navigation menu
    st.markdown("## 🧭 Sistema de Navegação")
    
    st.info("""
    **Bem-vindo ao FIDC Calculator!**
    
    Este sistema permite processar bases de dados de distribuidoras e calcular valores corrigidos 
    monetariamente com aplicação de IPCA e taxas de recuperação.
    
    **Fluxo do processo:**
    1.  **Carregamento** - Upload e análise dos arquivos Excel
    2. 🗺️ **Mapeamento** - Mapeamento automático e manual de campos
    3. 💰 **Correção** - Cálculo de aging, correção monetária e valor justo
    
    **👈 Use a navegação na barra lateral para acessar cada etapa.**
    """)
    
    # Quick stats se houver dados finais
    if 'df_final' in st.session_state and not st.session_state.df_final.empty:
        st.markdown("---")
        st.subheader("📈 Resumo Executivo")
        
        df_final = st.session_state.df_final
        
        # Calcular métricas principais
        total_valor_principal = df_final['valor_principal'].sum() if 'valor_principal' in df_final.columns else 0
        total_valor_corrigido = df_final['valor_corrigido'].sum() if 'valor_corrigido' in df_final.columns else 0
        total_valor_justo = df_final['valor_justo'].sum() if 'valor_justo' in df_final.columns else 0
        total_empresas = df_final['empresa'].nunique() if 'empresa' in df_final.columns else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💼 Empresas",
                total_empresas,
                help="Número de empresas processadas"
            )
        
        with col2:
            st.metric(
                "📊 Valor Principal",
                f"R$ {total_valor_principal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Valor total principal antes da correção"
            )
        
        with col3:
            st.metric(
                "⚡ Valor Corrigido",
                f"R$ {total_valor_corrigido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Valor total após correção monetária"
            )
        
        with col4:
            if total_valor_justo > 0:
                st.metric(
                    "💎 Valor Justo",
                    f"R$ {total_valor_justo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    help="Valor justo final com IPCA e taxa de recuperação"
                )
            else:
                st.metric(
                    "💎 Valor Justo",
                    "Pendente",
                    help="Aguardando cálculo do valor justo"
                )

if __name__ == "__main__":
    main()
