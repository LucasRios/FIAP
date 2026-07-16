# =============================================================================
# frontend/features/analise/page.py — Aula 13: tela de Análise de Sentimento
#
# Responsabilidade: exibir a interface (View). Esta camada SÓ desenha a tela;
# toda a comunicação com o back-end fica isolada no api_provider (Aula 13).
# Isso segue exatamente o mesmo padrão Feature-First da Aula 06 do semestre
# anterior — só trocamos "pipeline local" por "provider que fala HTTP".
#
# NOVO NESTA AULA: este arquivo inteiro, incluindo o uso de st.spinner e o
# tratamento de "resultado vazio" quando a API falha.
# =============================================================================

import streamlit as st
from providers import api_provider


def render():
    """Desenha a tela de Análise de Sentimento e trata a interação do usuário."""

    st.title("Análise de Sentimento")
    st.caption("Este front-end não roda nenhum modelo de IA localmente — ele "
               "apenas chama a API FastAPI construída na Aula 12.")

    texto = st.text_area("Digite o texto para análise:")

    # O botão só dispara a chamada de API quando clicado E se houver texto.
    if st.button("Analisar") and texto:

        # -------------------------------------------------------------
        # st.spinner — NOVO NESTA AULA
        # -------------------------------------------------------------
        # Enquanto o requests.post (dentro do api_provider) está esperando
        # a resposta do servidor, o usuário vê uma animação de carregamento
        # em vez de uma tela travada. Isso é a "Gestão de Expectativa e
        # Incerteza" que vimos na Aula 02 do Semestre 1, aplicada ao
        # consumo de API.
        with st.spinner("Analisando..."):
            resultado = api_provider.analisar_sentimento(texto)

        # Se a API falhou, api_provider já mostrou o st.error/st.warning
        # adequado — aqui só verificamos se HÁ resultado para exibir.
        if resultado:
            col1, col2 = st.columns(2)
            col1.metric("Sentimento", resultado["sentimento"])
            col2.metric("Confiança", f"{resultado['confianca']:.0%}")
