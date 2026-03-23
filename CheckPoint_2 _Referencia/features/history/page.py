# =============================================================================
# features/history/page.py — View da página de histórico
#
# Responsabilidade: exibir todas as análises realizadas na sessão atual,
# com tabela, gráfico de feedback e visualização de itens individuais.
# =============================================================================

import streamlit as st
import pandas as pd

from ui.charts import render_sentiment_chart


def render():
    """
    Renderiza a página de histórico de análises.

    Estrutura visual:
      [Tabela completa do histórico]
           ↓
      [Gráfico de distribuição de feedback] (se houver feedback)
           ↓
      [Visualização de análise individual selecionada]
    """

    st.title("Histórico de Análises")
    st.markdown("Consulte todas as notícias analisadas nesta sessão.")
    st.markdown("---")

    history = st.session_state.history

    # ------------------------------------------------------------------
    # Caso não haja histórico: exibe mensagem informativa
    # ------------------------------------------------------------------
    if len(history) == 0:
        st.info("Nenhuma análise registrada ainda. Vá para **Analisar notícia** para começar.")
        return

    # ------------------------------------------------------------------
    # Converte a lista de dicionários em DataFrame para exibição
    # ------------------------------------------------------------------
    df = pd.DataFrame(history)

    # Renomeia colunas para exibição mais amigável
    column_labels = {
        "url":        "URL",
        "summary":    "Resumo",
        "sentimento": "Sentimento",
        "feedback":   "Feedback",
    }
    df_display = df.rename(columns=column_labels)

    st.subheader(f"📊 {len(history)} análise(s) registrada(s)")
    st.dataframe(df_display, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Gráfico de distribuição de feedback (só aparece se houver feedback)
    # ------------------------------------------------------------------
    if "feedback" in df.columns:

        st.subheader("👍👎 Distribuição de Feedback")

        feedback_counts = (
            df["feedback"]
            .value_counts()
            .rename_axis("Tipo")
            .reset_index(name="Quantidade")
            .set_index("Tipo")
        )

        st.bar_chart(feedback_counts)

    # ------------------------------------------------------------------
    # Gráfico de distribuição de sentimentos
    # ------------------------------------------------------------------
    if "sentimento" in df.columns:

        st.subheader("🧠 Distribuição de Sentimentos")

        sentiment_counts = (
            df["sentimento"]
            .value_counts()
            .rename_axis("Sentimento")
            .reset_index(name="Quantidade")
            .set_index("Sentimento")
        )

        st.bar_chart(sentiment_counts)

        st.markdown("---")

        # 2. IMPLEMENTAÇÃO DO GRÁFICO
        st.markdown("---")
        st.subheader("Gráfico de Distribuição")
            
        # Chamamos a função da UI passando os dados do session_state
        # Contamos as ocorrências no DataFrame
        counts = df["sentimento"].value_counts().to_dict()
    
        # Mapeamos para o formato que a função da UI espera
        # (Ajuste as chaves para baterem com o que o provider usa: 'positive', etc)
        dist_global = {
            "positive": counts.get("Positivo", 0),
            "neutral": counts.get("Neutro", 0),
            "negative": counts.get("Negativo", 0)
        }

        if any(dist_global.values()):
            render_sentiment_chart(dist_global)
 
    # ------------------------------------------------------------------
    # Seletor para visualizar uma análise específica do histórico
    # ------------------------------------------------------------------
    st.subheader("🔎 Visualizar análise individual")

    # Cria rótulos amigáveis: "Análise 1 — https://..."
    options = {
        f"Análise {i + 1} — {row['url'][:60]}...": i
        for i, row in df.iterrows()
    }

    selected_label = st.selectbox("Selecionar análise", list(options.keys()))
    selected_idx   = options[selected_label]

    row = df.loc[selected_idx]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Sentimento", row.get("sentimento", "N/A"))

    with col2:
        st.metric("Feedback",   row.get("feedback",   "N/A"))

    st.subheader("Resumo")
    st.write(row["summary"])