# =============================================================================
# ui/sidebar.py — Componente de navegação lateral
#
# Responsabilidade: SOMENTE renderizar o menu e retornar qual página foi
# selecionada. Não contém lógica de negócio.
# A ideia é manter o roteamento centralizado e fácil de modificar.
# =============================================================================

import streamlit as st 

def render_sidebar():
    st.sidebar.title("🚀 FIAP AI News")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Navegação")
    
    # Criando botões que funcionam como links de navegação
    if st.sidebar.button("Analisar Notícia", use_container_width=True):
        st.session_state.page = "analysis"
    
    if st.sidebar.button("Histórico", use_container_width=True):
        st.session_state.page = "history"
        
    if st.sidebar.button("Configurações", use_container_width=True):
        st.session_state.page = "settings"
         
    
    return st.session_state.page