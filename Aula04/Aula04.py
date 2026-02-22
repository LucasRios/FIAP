import pandas as pd
import streamlit as st
import random
import time
import numpy as np
import plotly.express as px
import altair as alt

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(page_title="AI UX Demo", layout="wide")

# ==========================================================
# region INICIALIZAÇÃO DE ESTADO
# ==========================================================
if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []

if "analysis_ran" not in st.session_state:
    st.session_state.analysis_ran = False

if "config_version" not in st.session_state:
    st.session_state.config_version = 0

if "history_df" not in st.session_state:
    st.session_state.history_df = pd.DataFrame(
        columns=["Execução", "Classe", "Confiança (%)", "Modelo", "Threshold"]
    )
# endregion


# ==========================================================
# CALLBACK — RESET AO ALTERAR CONFIGURAÇÃO
# ==========================================================
def reset_analysis():
    st.session_state.analysis_ran = False
    st.session_state.last_result = None
    st.session_state.config_version += 1
    st.toast("Configuração alterada. Execute novamente.")


  
def simulate_model(model_type: str, threshold: float, _seed: int): 
    rng = random.Random(_seed)
    base_score = rng.uniform(0.4, 0.95)
    if model_type == "Avançado":
        base_score += 0.05
    score = min(base_score, 0.99)
    label = "Cachorro" if score >= threshold else "Gato"

    explanation = {
        "Formato das orelhas": round(rng.uniform(0.1, 0.4), 2),
        "Textura do pelo":      round(rng.uniform(0.1, 0.4), 2),
        "Formato do focinho":   round(rng.uniform(0.1, 0.4), 2),
    }
    return label, score, explanation

 
def build_explanation_df(explanation: dict) -> pd.DataFrame:
    """Transforma o dicionário de explicabilidade em DataFrame."""
    return pd.DataFrame(
        [{"Feature": k, "Peso": v} for k, v in explanation.items()]
    )


# ==========================================================
# SIDEBAR — CONTROLE DO SISTEMA
# ==========================================================
st.sidebar.header("Configurações do Modelo")

st.sidebar.selectbox(
    "Modelo",
    ["Base", "Avançado"],
    key="model_type",
    on_change=reset_analysis,
)

st.sidebar.slider(
    "Threshold de decisão",
    0.0, 1.0, 0.75,
    key="threshold",
    on_change=reset_analysis,
)

st.sidebar.checkbox(
    "Simular latência",
    value=True,
    key="simulate_latency",
)

st.sidebar.select_slider(
    "Nível de Verbosidade",
    options=["Baixa", "Média", "Alta", "Extrema"],
    key="verbosity_demo",
    on_change=reset_analysis,
)

st.sidebar.number_input(
    "Número de Épocas",
    min_value=1, max_value=1000, value=10, step=1,
    key="epochs_demo",
    on_change=reset_analysis,
)

st.sidebar.multiselect(
    "Selecionar Features do Modelo",
    ["Orelhas", "Pelo", "Focinho", "Cauda", "Porte"],
    default=["Orelhas", "Pelo"],
    key="features_demo",
    on_change=reset_analysis,
)

st.sidebar.text_input(
    "Prompt do Sistema",
    placeholder="Descreva como o modelo deve classificar...",
    key="prompt_demo",
    on_change=reset_analysis,
)

st.sidebar.text_area(
    "Observações adicionais",
    placeholder="Instruções complementares...",
    key="notes_demo",
    on_change=reset_analysis,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.info(
    "App de demo: classificação simulada com explicabilidade, "
    "human-in-the-loop e visualização de dados (Aula 04)."
)


# ==========================================================
# 1 — EMPTY STATE
# ==========================================================
st.title("Classificador de Imagem (Simulado)")

uploaded = st.file_uploader("Envie uma imagem", type=["png", "jpg", "jpeg"])

if not uploaded:
    st.info("Envie uma imagem para iniciar a análise.")
    st.stop()


# ==========================================================
# BOTÃO COMO GATILHO (AÇÃO, NÃO ESTADO)
# ==========================================================
if st.button("Executar Análise"):
    st.session_state.analysis_ran = True
    st.session_state.run_seed = int(time.time() * 1000) % 100_000


# ==========================================================
# EXECUÇÃO CONTROLADA PELO ESTADO
# ==========================================================
if st.session_state.analysis_ran:

    # --------------------------------------------------------
    # 2 — LOADING STATE / LATÊNCIA
    # --------------------------------------------------------
    if st.session_state.simulate_latency and "run_seed" not in st.session_state:
        pass  # já rodou antes, não repete spinner

    seed = st.session_state.get("run_seed", 42)

    # Só exibe spinners na primeira execução do seed atual
    if st.session_state.get("last_seed") != seed:
        if st.session_state.simulate_latency:
            with st.spinner("Extraindo características..."):
                time.sleep(1)
            with st.spinner("Classificando padrões..."):
                time.sleep(1)
            with st.spinner("Obtendo resultados..."):
                bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    bar.progress(i + 1)
            st.toast("Resultados consolidados.")
        st.session_state.last_seed = seed

    label, score, explanation = simulate_model(
        st.session_state.model_type,
        st.session_state.threshold,
        seed,
    )
    confidence_percent = int(score * 100)

    # Atualiza resultado e histórico apenas se for nova execução
    if st.session_state.last_result is None or st.session_state.last_result.get("seed") != seed:
        st.session_state.last_result = {
            "label": label, "score": score,
            "explanation": explanation, "seed": seed,
        }

        new_row = pd.DataFrame([{
            "Execução":       len(st.session_state.history) + 1,
            "Classe":         label,
            "Confiança (%)":  confidence_percent,
            "Modelo":         st.session_state.model_type,
            "Threshold":      st.session_state.threshold,
        }])
        st.session_state.history_df = pd.concat(
            [st.session_state.history_df, new_row], ignore_index=True
        )
        st.session_state.history.append({"label": label, "score": score})

    # ==========================================================
    # TABS DE RESULTADOS
    # ==========================================================
    tab_pred, tab_dados, tab_monitor = st.tabs([
        "Predição & Validação Humana",
        "Dados & Explicabilidade",
        "Monitoramento & Histórico",
    ])

    # ==========================================================
    # TAB 1 — PREDIÇÃO
    # ==========================================================
    with tab_pred:
        st.subheader("Resultado da Classificação")

        # ---- KPIs com delta (Aula 04 — st.metric) ----
        prev = st.session_state.history[-2]["score"] if len(st.session_state.history) >= 2 else None
        delta_val = f"{(score - prev) * 100:+.1f}%" if prev else None

        m1, m2, m3 = st.columns(3)
        m1.metric("Classe Prevista", label)
        m2.metric("Confiança", f"{confidence_percent}%", delta=delta_val)
        m3.metric(
            "Modelo",
            st.session_state.model_type,
            delta=f"Threshold: {st.session_state.threshold:.2f}",
        )

        st.progress(confidence_percent)

        if score >= 0.85:
            st.success("Alta confiança na previsão.")
        elif score >= 0.60:
            st.warning("Confiança moderada. Revisão recomendada.")
        else:
            st.error("Baixa confiança. Revisão humana necessária.")

        st.markdown("---")

        # ---- Human-in-the-loop ----
        st.subheader("Validação Humana")

        fc1, fc2 = st.columns(2)
        with fc1:
            if st.button("✅ IA acertou"):
                st.session_state.feedback_log.append(
                    {"result": label, "score": score, "correct": True}
                )
                st.success("Feedback registrado.")
        with fc2:
            if st.button("❌ IA errou"):
                st.session_state.feedback_log.append(
                    {"result": label, "score": score, "correct": False}
                )
                st.error("Feedback registrado.")

    # ==========================================================
    # TAB 2 — DADOS & EXPLICABILIDADE  (conceitos Aula 04)
    # ==========================================================
    with tab_dados:

        st.subheader("Inspeção dos Dados de Saída")

        # -- Histórico como DataFrame interativo com column_config --
        st.markdown("#### Histórico de execuções")
        st.caption(
            "Tabela interativa: ordene, redimensione e inspecione. "
            "A coluna *Confiança* é exibida como barra visual."
        )

        if not st.session_state.history_df.empty:
            # st.dataframe + column_config (Aula 04)
            st.dataframe(
                st.session_state.history_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Confiança (%)": st.column_config.ProgressColumn(
                        "Confiança (%)",
                        help="Score de confiança do modelo",
                        min_value=0,
                        max_value=100,
                        format="%d%%",
                    ),
                    "Threshold": st.column_config.NumberColumn(
                        "Threshold",
                        format="%.2f",
                    ),
                },
            )

            # Estatísticas descritivas (Aula 04 — df.describe())
            st.markdown("#### Estatísticas descritivas")
            st.caption(
                "Antes de confiar no gráfico, inspecione o dado bruto. "
                "`df.describe()` garante transparência."
            )
            st.dataframe(
                st.session_state.history_df[["Confiança (%)"]].describe().round(2),
                use_container_width=True,
            )

        st.markdown("---")

        # ---- Explicabilidade com Plotly (Aula 04) ----
        st.subheader("Explicabilidade Local")

        exp_df = build_explanation_df(explanation)

        # Gráfico de barras Plotly — interativo, com hover e exportação
        fig_exp = px.bar(
            exp_df,
            x="Peso",
            y="Feature",
            orientation="h",
            color="Peso",
            color_continuous_scale="Blues",
            title="Contribuição de cada feature para a decisão",
            labels={"Peso": "Peso relativo", "Feature": "Característica"},
            range_x=[0, 0.5],
        )
        fig_exp.update_layout(
            coloraxis_showscale=False,
            yaxis={"categoryorder": "total ascending"},
            height=280,
        )
        st.plotly_chart(fig_exp, use_container_width=True)

        # Tabela estática de resumo (Aula 04 — st.table para apresentação final)
        st.markdown("**Resumo da explicabilidade (tabela estática)**")
        st.table(exp_df.set_index("Feature").rename(columns={"Peso": "Peso relativo"}))

    # ==========================================================
    # TAB 3 — MONITORAMENTO & HISTÓRICO  (Aula 04 — gráficos nativos + Altair)
    # ==========================================================
    with tab_monitor:
        st.subheader("Monitoramento do Sistema")

        total_fb = len(st.session_state.feedback_log)

        if total_fb > 0:
            correct = sum(1 for f in st.session_state.feedback_log if f["correct"])
            accuracy = correct / total_fb

            mon1, mon2, mon3 = st.columns(3)
            mon1.metric("Feedbacks recebidos", total_fb)
            mon2.metric("Acertos", correct)
            mon3.metric("Acurácia percebida", f"{int(accuracy * 100)}%")

            if accuracy < 0.7:
                st.warning("⚠️ Possível degradação do modelo detectada.")
        else:
            st.info("Ainda não há feedback suficiente para monitoramento.")

        st.markdown("---")

        # ---- Gráfico nativo: evolução da confiança (Aula 04 — st.line_chart) ----
        if len(st.session_state.history) > 1:
            st.markdown("#### Evolução da confiança por execução")
            st.caption(
                "Gráfico nativo do Streamlit (`st.line_chart`): "
                "ideal para prototipação rápida de séries temporais."
            )
            conf_series = pd.DataFrame(
                {"Confiança (%)": [int(h["score"] * 100) for h in st.session_state.history]},
                index=range(1, len(st.session_state.history) + 1),
            )
            conf_series.index.name = "Execução"
            st.line_chart(conf_series)

        # ---- Altair: distribuição de classes (Aula 04 — st.altair_chart) ----
        if len(st.session_state.history) >= 2:
            st.markdown("#### Distribuição de classes previstas")
            st.caption(
                "Gráfico Altair com gramática declarativa: "
                "mapeia categoria → cor → contagem de forma explícita."
            )

            hist_df = pd.DataFrame(st.session_state.history)
            class_counts = (
                hist_df.groupby("label")
                .size()
                .reset_index(name="Contagem")
            )

            chart_classes = (
                alt.Chart(class_counts)
                .mark_bar()
                .encode(
                    x=alt.X("label:N", title="Classe"),
                    y=alt.Y("Contagem:Q", title="Número de predições"),
                    color=alt.Color("label:N", legend=None),
                    tooltip=["label", "Contagem"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart_classes, use_container_width=True)

        # ---- Plotly: scatter histórico — confiança vs execução ----
        if len(st.session_state.history) >= 3:
            st.markdown("#### Scatter: confiança × execução por classe")
            st.caption(
                "Plotly `px.scatter`: interativo, com hover nativo e "
                "legenda clicável para filtrar classes."
            )

            scatter_df = st.session_state.history_df.copy()
            fig_scatter = px.scatter(
                scatter_df,
                x="Execução",
                y="Confiança (%)",
                color="Classe",
                symbol="Modelo",
                hover_data=["Threshold"],
                title="Histórico de predições",
                height=320,
            )
            fig_scatter.add_hline(
                y=int(st.session_state.threshold * 100),
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Threshold ({int(st.session_state.threshold*100)}%)",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # ---- Filtro interativo com botão (Aula 04 — padrão slider + botão) ----
        if not st.session_state.history_df.empty:
            st.markdown("---")
            st.markdown("#### Filtrar histórico por confiança mínima")
            st.caption(
                "O filtro pesado só é aplicado ao clicar em **Aplicar**, "
                "evitando reprocessamento a cada ajuste do slider."
            )

            min_conf = st.slider(
                "Confiança mínima (%)",
                0, 100, 50,
                key="min_conf_filter",
            )

            if st.button("Aplicar filtro"):
                filtered = st.session_state.history_df[
                    st.session_state.history_df["Confiança (%)"] >= min_conf
                ]
                st.session_state["filtered_history"] = filtered

            if "filtered_history" in st.session_state:
                st.dataframe(
                    st.session_state["filtered_history"],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Confiança (%)": st.column_config.ProgressColumn(
                            "Confiança (%)", min_value=0, max_value=100, format="%d%%"
                        )
                    },
                )

else:
    st.info("Configure os parâmetros e clique em **Executar Análise**.")