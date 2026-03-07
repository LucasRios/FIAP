import streamlit as st
import pandas as pd

def render():

    st.title("Histórico de análises")

    history = st.session_state.history

    if len(history) == 0:
        st.info("Nenhuma análise registrada.")
        return

    df = pd.DataFrame(history)

    st.subheader("Histórico completo")

    st.dataframe(df)

    st.markdown("---")

    # ==========================
    # Gráfico de feedback
    # ==========================

    if "feedback" in df.columns:

        st.subheader("Distribuição de Feedback")

        feedback_counts = (
            df["feedback"]
            .value_counts()
            .rename_axis("Tipo")
            .reset_index(name="Quantidade")
        )

        feedback_counts = feedback_counts.set_index("Tipo")

        st.bar_chart(feedback_counts)

    st.markdown("---")

    # ==========================
    # Visualizar resumo salvo
    # ==========================

    idx = st.selectbox(
        "Selecionar análise",
        df.index
    )

    st.subheader("Resumo")

    st.write(df.loc[idx]["summary"])