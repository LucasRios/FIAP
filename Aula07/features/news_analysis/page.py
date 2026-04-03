import streamlit as st
from pipelines.news_pipeline import analyze_news

def render():
    st.title("Análise de Notícias com IA")
    st.markdown("insira a url da notícia que deseja analisar")
    st.markdown("---")

    st.subheader("URL da Notícia")
    st.text_input("Digite a URL da notícia aqui",
                        placeholder="https://www.cnnbrasil.com.br/...",
                        key="url_input")

    st.button("Analisar", on_click=run_analysis)
  
    if not st.session_state.summary:
        st.warning("Insira uma URL válida para análise.")
        return
    
    tab_sentiment, tab_summary, tab_raw = st.tabs(["Sentimento", "Resumo", "texto completo"])

    with tab_sentiment:
        st.subheader("Análise de Sentimento")
        sentiment = st.session_state.sentiment
        if sentiment:
            st.write(f"O sentimento da notícia é: **{sentiment['emoji']}**")


    with tab_summary:
        st.subheader("Resumo da Notícia")
        summary = st.session_state.summary
        if summary:
            st.write(f"O resumo da notícia é: **{summary}**")

    with tab_raw:
        st.subheader("Texto Completo da Notícia")
        article = st.session_state.article
        if article:
            st.write(f"O texto completo da notícia é: **{article}**")
        






def run_analysis():    
    url = st.session_state.get("url_input", "").strip()

    if not url:
        st.warning("Por favor, insira uma URL válida.")
        return
    
    resultado_analise = analyze_news(url)

    print (resultado_analise)

    if resultado_analise:
        st.session_state.article = resultado_analise['article']
        st.session_state.summary = resultado_analise['summary']
        st.session_state.sentiment = resultado_analise['sentiment']        
    else:
        st.warning("Não foi possível analisar a notícia. Verifique a URL e tente novamente.")