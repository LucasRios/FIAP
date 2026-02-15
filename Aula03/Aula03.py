import streamlit as st
import random
import time
import numpy as np

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(page_title="AI UX Demo", layout="wide")

# ==========================================================
#region INICIALIZAÇÃO DE ESTADO
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
#endregion
# ==========================================================

# ==========================================================
# CALLBACK — RESET AO ALTERAR CONFIGURAÇÃO
# ==========================================================
def reset_analysis():
    st.session_state.analysis_ran = False
    st.session_state.last_result = None
    st.session_state.config_version += 1
    st.toast("Configuração alterada. Execute novamente.")


# ==========================================================
# SIMULAÇÃO DO MODELO
# ==========================================================
def simulate_model(model_type, threshold):
    base_score = random.uniform(0.4, 0.95)

    if model_type == "Avançado":
        base_score += 0.05

    score = min(base_score, 0.99)
    label = "Cachorro" if score >= threshold else "Gato"

    explanation = {
        "Formato das orelhas": np.round(random.uniform(0.1, 0.4), 2),
        "Textura do pelo": np.round(random.uniform(0.1, 0.4), 2),
        "Formato do focinho": np.round(random.uniform(0.1, 0.4), 2),
    }

    return label, score, explanation


# ==========================================================
# SIDEBAR — CONTROLE DO SISTEMA (Widgets como estado)
# ==========================================================
st.sidebar.header("Configurações do Modelo")

# --------------------------------------------------
# region CONTROLES  — Widgets que alteram o estado e resetam a análise
# --------------------------------------------------

st.sidebar.selectbox(
    "Modelo",
    ["Base", "Avançado"],
    key="model_type",
    on_change=reset_analysis
)

st.sidebar.slider(
    "Threshold de decisão",
    0.0, 1.0, 0.75,
    key="threshold",
    on_change=reset_analysis
)

st.sidebar.checkbox(
    "Simular latência",
    value=True,
    key="simulate_latency"
)

st.sidebar.select_slider(
    "Nível de Verbosidade",
    options=["Baixa", "Média", "Alta", "Extrema"],
    key="verbosity_demo",
    on_change=reset_analysis
)

st.sidebar.number_input(
    "Número de Épocas",
    min_value=1,
    max_value=1000,
    value=10,
    step=1,
    key="epochs_demo",
    on_change=reset_analysis
)
 
st.sidebar.multiselect(
    "Selecionar Features do Modelo",
    ["Orelhas", "Pelo", "Focinho", "Cauda", "Porte"],
    default=["Orelhas", "Pelo"],
    key="features_demo",
    on_change=reset_analysis
)
 
st.sidebar.text_input(
    "Prompt do Sistema",
    placeholder="Descreva como o modelo deve classificar...",
    key="prompt_demo",
    on_change=reset_analysis
)

st.sidebar.text_area(
    "Observações adicionais",
    placeholder="Instruções complementares...",
    key="notes_demo",
    on_change=reset_analysis
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.info(
    "Este app simula comportamento probabilístico, "
    "explicabilidade e human-in-the-loop."
)
#endregion
# ==========================================================


# ==========================================================
# 1 - EMPTY STATE
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

# ==========================================================
# EXECUÇÃO CONTROLADA PELO ESTADO
# ==========================================================
if st.session_state.analysis_ran:

    # -------------------------------
    # 2 - LOADING STATE / LATÊNCIA
    # -------------------------------
    if st.session_state.simulate_latency:
        with st.spinner("Extraindo características..."):
            time.sleep(1)

        with st.spinner("Classificando padrões..."):
            time.sleep(1)

        with st.spinner("Obtendo resultados..."):
            progress_bar = st.progress(0)
            total_steps = 100
            for i in range(total_steps):
                time.sleep(0.02)
                progress_bar.progress(i + 1)

        st.toast("Resultados consolidados.")
 
    label, score, explanation = simulate_model(
        st.session_state.model_type,
        st.session_state.threshold
    )

    confidence_percent = int(score * 100)

    st.session_state.last_result = {
        "label": label,
        "score": score,
        "explanation": explanation
    }

    st.session_state.history.append({
        "label": label,
        "score": score
    })

    # ==========================================================
    # TABS DE RESULTADOS
    # ==========================================================
    tab_predicao, tab_monitoramento = st.tabs(
        ["Predição & Validação Humana", "Monitoramento & Histórico"]
    )

    # ==========================================================
    # TAB 1 — PREDIÇÃO
    # ==========================================================
    with tab_predicao:

        # -------------------------------
        # 3 - CONFIDENCE UI
        # -------------------------------
        st.subheader("Resultado da Classificação")

        row1_col1, row1_col2 = st.columns([1, 2])

        with row1_col1:
            st.metric("Classe Prevista", label)
            st.metric("Confiança", f"{confidence_percent}%")
            st.progress(confidence_percent)

        with row1_col2:
            if score >= 0.85:
                st.success("Alta confiança na previsão.")
            elif score >= 0.60:
                st.warning("Confiança moderada. Revisão recomendada.")
            else:
                st.error("Baixa confiança. Revisão humana necessária.")

        st.markdown("---")

        # -------------------------------
        # 4 - EXPLICABILIDADE
        # -------------------------------
        st.subheader("Explicabilidade Local")

        exp_col1, exp_col2 = st.columns(2)

        features = list(explanation.items())

        with exp_col1:
            for feature, weight in features[:2]:
                st.write(feature)
                st.progress(int(weight * 100))

        with exp_col2:
            for feature, weight in features[2:]:
                st.write(feature)
                st.progress(int(weight * 100))

        st.markdown("---")

        # -------------------------------
        # 5 - HUMAN IN THE LOOP
        # -------------------------------
        st.subheader("Validação Humana")

        feedback_col1, feedback_col2 = st.columns(2)

        with feedback_col1:
            if st.button("IA acertou"):
                st.session_state.feedback_log.append({
                    "result": label,
                    "score": score,
                    "correct": True
                })
                st.success("Feedback registrado.")

        with feedback_col2:
            if st.button("IA errou"):
                st.session_state.feedback_log.append({
                    "result": label,
                    "score": score,
                    "correct": False
                })
                st.error("Feedback registrado.")

    # ==========================================================
    # TAB 2 — MONITORAMENTO & HISTÓRICO
    # ==========================================================
    with tab_monitoramento:

        st.subheader("Monitoramento do Sistema")

        total = len(st.session_state.feedback_log)

        if total > 0:
            correct = sum(1 for f in st.session_state.feedback_log if f["correct"])
            accuracy = correct / total

            monitor_col1, monitor_col2 = st.columns(2)

            with monitor_col1:
                st.metric("Feedbacks recebidos", total)

            with monitor_col2:
                st.metric("Acurácia percebida", f"{int(accuracy*100)}%")

            if accuracy < 0.7:
                st.warning("Possível degradação do modelo detectada.")
        else:
            st.info("Ainda não há feedback suficiente para monitoramento.")

        st.markdown("---")

        # -------------------------------
        # HISTÓRICO
        # -------------------------------
        st.subheader("Histórico de Decisões")

        history_cols = st.columns(2)
        recent = st.session_state.history[-6:]

        for i, item in enumerate(recent):
            with history_cols[i % 2]:
                st.write(f"{item['label']} — {int(item['score']*100)}%")

else:
    st.info("Configure os parâmetros e clique em **Executar Análise**.")