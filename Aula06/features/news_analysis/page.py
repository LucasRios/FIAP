# =============================================================================
# features/news_analysis/page.py — View da página de análise de notícias
#
# Responsabilidade: renderizar a interface de análise. Esta camada SÓ lida
# com exibição
# =============================================================================

import streamlit as st 
from pipelines.news_pipeline import analyze_news
from ui.charts import render_sentiment_chart


def render():
    """
    Renderiza a página principal de análise de notícias.

    Estrutura visual:
      [Input de URL] + [Botão Analisar]
           ↓
      [Tabs: Sentimento | Resumo | Texto extraído]
           ↓
      [Seção de Feedback]
    """

    st.title("🔍 Análise de Notícias com IA")
    st.markdown("Insira a URL de uma notícia e a IA irá extrair, processar e analisar o conteúdo.")
    st.markdown("---")

    # ------------------------------------------------------------------
    # Seção de input
    # ------------------------------------------------------------------
    st.subheader("1. Informe a URL")

    url = st.text_input(
        "URL da notícia",
        placeholder="https://g1.globo.com/...",
        key="url_input"    # chave no session_state
    )

    # on_click= passa a função sem chamá-la; o Streamlit chama ao clicar
    st.button(
        "🚀 Executar análise",
        on_click=run_analysis,
        type="primary"
    )

    # ------------------------------------------------------------------
    # Se ainda não há resultado, exibe instrução e encerra a renderização
    # ------------------------------------------------------------------
    if not st.session_state.summary:
        st.info("⬆️ Insira uma URL acima e clique em **Executar análise** para começar.")
        return

    st.markdown("---")
    st.subheader("2. Resultados")

    # ------------------------------------------------------------------
    # Tabs de resultado: Sentimento | Resumo | Texto bruto
    # ------------------------------------------------------------------
    tab_sentiment, tab_summary, tab_raw = st.tabs([
        "🧠 Sentimento",
        "📝 Resumo",
        "📄 Texto extraído",
    ])

    # ---- Tab 1: Análise de Sentimento --------------------------------
    with tab_sentiment:

        sentiment = st.session_state.sentiment

        if sentiment:
            st.subheader("Sentimento detectado na notícia")

            # Exibe o sentimento em destaque com métricas do Streamlit
            col_emoji, col_label, col_score = st.columns([1, 2, 2])

            with col_emoji:
                # Emoji grande como destaque visual
                st.markdown(
                    f"<h1 style='text-align:center'>{sentiment['emoji']}</h1>",
                    unsafe_allow_html=True
                )

            with col_label:
                st.metric(
                    label="Classificação",
                    value=sentiment["label"]
                )

            with col_score:
                st.metric(
                    label="Confiança do modelo",
                    value=f"{abs(sentiment['score']) * 100:.0f}%"
                )

            # Barra de progresso visual para o score de confiança
            st.progress(abs(sentiment["score"]))

            st.caption(
                "ℹ️ A análise de sentimento indica o tom predominante da notícia "
                "com base no conteúdo textual extraído."
            )
 
        else:
            st.info("Sentimento não disponível para esta análise.")

    # ---- Tab 2: Resumo com efeito de streaming ----------------------
    with tab_summary:

        st.subheader("Resumo gerado pelo modelo")

        # Simula efeito de streaming: exibe palavra por palavra
        # Em produção com API real, usaríamos stream=True e iteraríamos
        # sobre os chunks retornados pelo modelo
        placeholder = st.empty()
        displayed_text = ""

        for word in st.session_state.summary.split():
            displayed_text += word + " "
            placeholder.write(displayed_text)

        st.markdown("---")

        # ---- Seção de feedback ------------------------------------
        st.subheader("📊 Esse resumo foi útil?")

        col_pos, col_neg = st.columns(2)

        with col_pos:
            if st.button("👍 Útil"):
                _save_feedback("positivo")
                st.success("Obrigado pelo feedback positivo!")

        with col_neg:
            if st.button("👎 Ruim"):
                _save_feedback("negativo")
                st.error("Obrigado por nos avisar! Vamos melhorar.")

    # ---- Tab 3: Texto bruto extraído --------------------------------
    with tab_raw:

        st.subheader("Texto extraído da notícia")
        st.caption("Conteúdo bruto capturado pelo scraper antes do processamento.")

        st.text_area(
            "Conteúdo",
            value=st.session_state.article_text,
            height=350,
            disabled=True     # somente leitura
        )


# =============================================================================
# Função auxiliar (privada, prefixo _) — salva feedback no histórico
# =============================================================================

def _save_feedback(feedback_type: str):
    """
    Salva a análise atual + feedback no histórico da sessão.

    Args:
        feedback_type (str): "positivo" ou "negativo"
    """
    st.session_state.history.append({
        "url":       st.session_state.current_url,
        "summary":   st.session_state.summary,
        "sentimento": st.session_state.sentiment["label"] if st.session_state.sentiment else "N/A",
        "feedback":  feedback_type,
    })

 
def run_analysis():
    """
    Callback chamado quando o usuário clica em "Executar análise".

    O Streamlit passa funções de callback para on_click= dos botões.
    Nesse momento, st.session_state.url_input já tem o valor digitado.

    Fluxo:
      1. Lê a URL do session_state (espelho do widget)
      2. Valida se a URL foi preenchida
      3. Chama a pipeline de análise
      4. Salva os resultados no session_state para a View exibir
    """

    url = st.session_state.get("url_input", "").strip()
    if not url:
        st.warning("Insira uma URL.")
        return

    # Chama o pipeline (que agora está em /pipelines)
    result = analyze_news(url=url)

    if result:
        st.session_state.article_text = result["article"]
        st.session_state.summary      = result["summary"]
        st.session_state.sentiment    = result["sentiment"]
        st.session_state.current_url  = url
    else:
        st.error("Não foi possível analisar esta URL.")