# =============================================================================
# features/settings/page.py — View da página de configurações
#
# Responsabilidade: permitir ao usuário ajustar os parâmetros do modelo.
# Os widgets usam key= para escrever diretamente no st.session_state,
# eliminando a necessidade de um controller separado para esta página.
# =============================================================================

import streamlit as st


def render():
    """
    Renderiza a página de configurações do modelo.

    Qualquer alteração aqui é imediatamente refletida em
    st.session_state.model e st.session_state.temperature,
    que são lidos pelo controller de análise.
    """

    st.title("⚙️ Configurações")
    st.markdown("Ajuste os parâmetros do modelo de linguagem.")
    st.markdown("---")

    # ------------------------------------------------------------------
    # Seleção do modelo
    # ------------------------------------------------------------------
    st.subheader("🤖 Modelo")

    st.selectbox(
        "Escolher modelo",
        options=["small", "medium", "large"],
        key="model",         # lê/escreve em st.session_state.model
        help=(
            "small: mais rápido, menos preciso\n"
            "medium: equilíbrio entre velocidade e qualidade\n"
            "large: mais lento, maior qualidade"
        )
    )

    # ------------------------------------------------------------------
    # Parâmetros de geração
    # ------------------------------------------------------------------
    st.subheader("🎛️ Parâmetros de geração")

    st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        key="temperature",   # lê/escreve em st.session_state.temperature
        help=(
            "Controla a 'criatividade' do modelo.\n"
            "0.0 = respostas determinísticas\n"
            "1.0 = respostas mais variadas e criativas"
        )
    )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Utilitários de cache
    # ------------------------------------------------------------------
    st.subheader("🗑️ Cache")
    st.caption(
        "O Streamlit armazena em cache resultados de scraping e LLM "
        "para evitar requisições repetidas. Limpe se precisar forçar "
        "uma nova análise de uma URL já processada."
    )

    if st.button("Limpar cache", type="secondary"):
        st.cache_data.clear()
        st.success("✅ Cache limpo com sucesso!")