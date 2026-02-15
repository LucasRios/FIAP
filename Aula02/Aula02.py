import streamlit as st
import random
import time
import numpy as np

# -------------------------------
# CONFIGURAÇÕES AUXILIARES PARA RODAR
# ------------------------------- 
if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []
 
def simulate_model(model_type):
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







# -------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------
st.set_page_config(page_title="AI UX Demo", layout="wide")
 
# -------------------------------
# SIDEBAR — CONTROLE DO SISTEMA
# -------------------------------
st.sidebar.header("Configurações do Modelo")

model_type = st.sidebar.selectbox(
    "Modelo",
    ["Base", "Avançado"]
)

threshold = st.sidebar.slider(
    "Threshold de decisão",
    0.0, 1.0, 0.75
)

simulate_latency = st.sidebar.checkbox("Simular latência", True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.info(
    "Este app simula comportamento probabilístico, "
    "explicabilidade e human-in-the-loop."
)

# -------------------------------
# 1 - Empty state
# -------------------------------
st.title("Classificador de Imagem (Simulado) - 1 - Empty state")

uploaded = st.file_uploader("Envie uma imagem", type=["png", "jpg", "jpeg"])

if not uploaded:
    st.info("Envie uma imagem para iniciar a análise.")
    st.stop()

# -------------------------------
# 2 - Loading State | Design para Latência - PROCESSAMENTO
# -------------------------------
if simulate_latency:
    with st.spinner("Extraindo características... 2 - Loading State"):
        time.sleep(1)
    with st.spinner("Classificando padrões... 2 - Loading State"):
        time.sleep(1)
    with st.spinner("Obtendo resultados... 3 - Design para Latência"):
        progress_bar = st.progress(0)
        status_text = st.empty() 
        total_steps = 100 
        for i in range(total_steps):
            time.sleep(0.03)  # latência maior aqui
            progress_bar.progress(i + 1)

        st.success("Resultados consolidados.")      


label, score, explanation = simulate_model(model_type)

st.session_state.last_result = {
    "label": label,
    "score": score,
    "explanation": explanation
}

confidence_percent = int(score * 100)

# ==========================================================
# TABS DE RESULTADOS
# ==========================================================
tab_predicao, tab_monitoramento = st.tabs(
    ["Predição & Validação Humana", "Monitoramento & Histórico"]
)
 
with tab_predicao:

    # -------------------------------
    # 3 - Confidence UI 
    # -------------------------------
    st.subheader("Resultado da Classificação - 3 - Confidence UI ")

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
    st.subheader("Explicabilidade Local - 4 - EXPLICABILIDADE")

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
    st.subheader("Validação Humana - 5 - HUMAN IN THE LOOP")

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

    st.session_state.history.append({
        "label": label,
        "score": score
    })

    history_cols = st.columns(2)

    recent = st.session_state.history[-6:]

    for i, item in enumerate(recent):
        with history_cols[i % 2]:
            st.write(f"{item['label']} — {int(item['score']*100)}%")