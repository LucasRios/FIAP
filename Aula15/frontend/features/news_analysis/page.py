# =============================================================================
# frontend/features/news_analysis/page.py — Aula 15
#
# Responsabilidade: interface de análise de notícias do Sprint, agora falando
# com a API em vez do pipeline local. Compare com o page.py da Aula 06 —
# a única mudança real é de onde vem "resultado".
#
# NOVO NESTA AULA: as abas (tabs) para escolher entre analisar por URL ou
# colar o texto direto, e a função auxiliar _exibir_resultado compartilhada.
# =============================================================================

import streamlit as st
from providers import api_provider


def render():
    st.subheader("Análise de Notícia")

    # st.tabs cria duas abas na mesma tela — o usuário escolhe o caminho
    # mais conveniente sem precisar de duas páginas separadas.
    aba_url, aba_texto = st.tabs(["Analisar por URL", "Colar texto"])

    with aba_url:
        url = st.text_input("URL da notícia:")
        if st.button("Analisar URL") and url:
            with st.spinner("Analisando..."):
                resultado = api_provider.analisar_noticia(url=url)
            _exibir_resultado(resultado)

    with aba_texto:
        texto = st.text_area("Cole o texto da notícia:", height=200)
        if st.button("Analisar Texto") and texto:
            with st.spinner("Analisando..."):
                resultado = api_provider.analisar_noticia(texto=texto)
            _exibir_resultado(resultado)


def _exibir_resultado(resultado: dict | None):
    """Desenha o resultado da análise — reaproveitada pelas duas abas acima."""
    if not resultado:
        # api_provider já mostrou a mensagem de erro adequada; aqui só
        # evitamos tentar desenhar um resultado que não existe.
        return

    col1, col2 = st.columns(2)
    col1.metric("Sentimento", resultado["sentimento"])
    col2.metric("Confiança", f"{resultado['confianca']:.0%}")

    st.markdown("### Resumo")
    st.write(resultado["resumo"])

    if resultado["entidades"]:
        st.markdown("### Entidades detectadas")
        st.write(", ".join(resultado["entidades"]))
