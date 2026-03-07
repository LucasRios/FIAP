import streamlit as st
from .controller import run_analysis

def render():

    st.title("Análise de Notícias com IA")

    url = st.text_input(
        "URL da notícia",
        key="url_input"
    )

    st.button(
        "Executar análise",
        on_click=run_analysis
    )

    if not st.session_state.summary:
        st.info("Insira uma URL para iniciar.")
        return

    tab1, tab2  = st.tabs([
        "Resumo",
        "Texto extraído" 
    ])

    with tab1:

        st.subheader("Resumo da notícia")

        placeholder = st.empty()

        text = ""

        for word in st.session_state.summary.split():
            text += word + " "
            placeholder.write(text)

        st.subheader("Feedback")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👍 útil"): 
                st.session_state.history.append({
                    "url": st.session_state.current_url,
                    "summary": st.session_state.summary,
                    "feedback": "positivo"
                })
                st.success("Obrigado pelo feedback!")

        with col2:
            if st.button("👎 ruim"): 
                st.session_state.history.append({
                    "url": st.session_state.current_url,
                    "summary": st.session_state.summary,
                    "feedback": "negativo"
                }) 
                st.error("Obrigado pelo feedback!")           

    with tab2:

        st.subheader("Texto da notícia")

        st.text_area(
            "Conteúdo",
            st.session_state.article_text,
            height=300
        )