import streamlit as st

def render():

    st.title("Configurações")

    st.subheader("Modelo")

    st.selectbox(
        "Escolher modelo",
        ["small", "medium", "large"],
        key="model"
    )

    st.subheader("Parâmetros")

    st.slider(
        "Temperatura",
        0.0,
        1.0,
        key="temperature"
    )

    if st.button("Limpar cache"):

        st.cache_data.clear()

        st.success("Cache limpo.")