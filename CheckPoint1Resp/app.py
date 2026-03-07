import os
import json
import io
import time
import numpy as np
import pandas as pd
import streamlit as st
import tensorflow as tf
import plotly.express as px
import altair as alt
from PIL import Image

# ==============================================
# App Streamlit para VAE PneumoniaMNIST
# ==============================================
# Funcionalidades:
# - Triagem de pneumonia baseada no erro de reconstrução
# - Geração de novas imagens de raio-X
# - Upload e reconstrução de imagens
# ==============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
WEIGHTS_PATH = os.path.join(MODELS_DIR, 'vae_pneumonia.weights.h5')
CONFIG_PATH = os.path.join(MODELS_DIR, 'config.json')


class Sampling(tf.keras.layers.Layer):
    def call(self, inputs, **kwargs):
        z_mean, z_log_var = inputs
        epsilon = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon


def build_encoder(latent_dim: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(28, 28, 1))
    x = tf.keras.layers.Conv2D(32, kernel_size=3, strides=2, padding='same', activation='relu')(inputs)
    x = tf.keras.layers.Conv2D(64, kernel_size=3, strides=2, padding='same', activation='relu')(x)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(128, activation='relu')(x)
    z_mean = tf.keras.layers.Dense(latent_dim, name='z_mean')(x)
    z_log_var = tf.keras.layers.Dense(latent_dim, name='z_log_var')(x)
    z = Sampling()([z_mean, z_log_var])
    return tf.keras.Model(inputs, [z_mean, z_log_var, z], name='encoder')


def build_decoder(latent_dim: int) -> tf.keras.Model:
    latent_inputs = tf.keras.Input(shape=(latent_dim,))
    x = tf.keras.layers.Dense(7 * 7 * 64, activation='relu')(latent_inputs)
    x = tf.keras.layers.Reshape((7, 7, 64))(x)
    x = tf.keras.layers.Conv2DTranspose(64, kernel_size=3, strides=2, padding='same', activation='relu')(x)
    x = tf.keras.layers.Conv2DTranspose(32, kernel_size=3, strides=2, padding='same', activation='relu')(x)
    outputs = tf.keras.layers.Conv2DTranspose(1, kernel_size=3, padding='same', activation='sigmoid')(x)
    return tf.keras.Model(latent_inputs, outputs, name='decoder')


class VAE(tf.keras.Model):
    def __init__(self, encoder: tf.keras.Model, decoder: tf.keras.Model, **kwargs):
        super().__init__(**kwargs)
        self.encoder = encoder
        self.decoder = decoder

    def call(self, inputs, training=False):
        z_mean, z_log_var, z = self.encoder(inputs, training=training)
        reconstruction = self.decoder(z, training=training)
        return reconstruction

    def encode(self, inputs, training=False):
        return self.encoder(inputs, training=training)

    def decode(self, z, training=False):
        return self.decoder(z, training=training)

@st.cache_resource
def load_model():
    if not os.path.exists(CONFIG_PATH) or not os.path.exists(WEIGHTS_PATH):
        return None, 'Pesos ou configuração não encontrados. Treine o modelo executando train_vae.py.'
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    latent_dim = int(config.get('latent_dim', 16))
    encoder = build_encoder(latent_dim)
    decoder = build_decoder(latent_dim)
    vae = VAE(encoder, decoder)
    # Construir o modelo chamando uma passagem dummy antes de carregar pesos
    dummy = tf.zeros((1, 28, 28, 1))
    _ = vae(dummy, training=False)
    vae.load_weights(WEIGHTS_PATH)
    return vae, None


def preprocess_image(image: Image.Image) -> np.ndarray:
    # Converter para grayscale e 28x28
    if image.mode != 'L':
        image = image.convert('L')
    if image.size != (28, 28):
        image = image.resize((28, 28))
    arr = np.array(image).astype('float32')
    if arr.max() > 1.0:
        arr = arr / 255.0
    arr = np.expand_dims(arr, axis=-1)  # (28,28,1)
    arr = np.expand_dims(arr, axis=0)   # (1,28,28,1)
    return arr

@st.cache_data
def compute_reconstruction_error(x: np.ndarray, x_recon: np.ndarray) -> float:
    # Erro MSE por imagem
    return float(np.mean((x - x_recon) ** 2))

@st.cache_data
def classify_pneumonia(reconstruction_error: float, threshold_normal: float, threshold_borderline: float) -> tuple:
    """
    Classifica se há possível pneumonia baseado no erro de reconstrução.
    Erro alto = possível pneumonia (imagem fora do padrão normal aprendido).
    """
    if reconstruction_error < threshold_normal:
        return "NORMAL", "Baixo risco de pneumonia", "green"
    elif reconstruction_error < threshold_borderline:
        return "BORDERLINE", "Risco moderado - recomenda-se avaliação médica", "orange"
    else:
        return "POSSÍVEL PNEUMONIA", "Alto risco - urgente avaliação médica", "red"


def generate_new_images(vae: VAE, num_images: int = 4) -> np.ndarray:
    """Gera novas imagens de raio-X usando o VAE treinado."""
    latent_dim = vae.encoder.output_shape[0][-1]  # Pega a dimensão do z_mean
    
    # Amostrar do espaço latente normal padrão
    z_samples = np.random.normal(0, 1, (num_images, latent_dim))
    
    # Decodificar para gerar imagens
    generated_images = vae.decode(z_samples, training=False).numpy()
    
    return generated_images


st.set_page_config(page_title='VAE PneumoniaMNIST - Triagem e Geração', layout='wide')


# ==========================================================
# INICIALIZAÇÃO DE ESTADO
# ==========================================================
if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []

if "analysis_ran" not in st.session_state:
    st.session_state.analysis_ran = False

if "generated_images" not in st.session_state:
    st.session_state.generated_images = None

if "num_generated" not in st.session_state:
    st.session_state.num_generated = 4

if "history_df" not in st.session_state:
    st.session_state.history_df = pd.DataFrame(
        columns=["Execução", "Classificação", "Erro MSE", "Confiança (%)"]
    )

# ==========================================================
# CALLBACK — RESET AO ALTERAR CONFIGURAÇÃO
# ==========================================================
def reset_analysis():
    st.session_state.analysis_ran = False
    st.session_state.last_result = None
    st.toast("Configuração alterada. Execute novamente.")



# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.header("Modelo VAE")
vae, err = load_model()
if err:
    st.sidebar.error(err)
    st.stop()
else:
    st.sidebar.success("✅ Modelo carregado com sucesso!")
    st.sidebar.info(f"Dimensão latente: {vae.encoder.output_shape[0][-1]}")

st.sidebar.markdown("---")
st.sidebar.header("Configurações de Triagem")

st.sidebar.slider(
    "Threshold Normal (MSE)",
    min_value=0.000, max_value=0.050, value=0.010, step=0.001,
    format="%.3f",
    key="threshold_normal",
    on_change=reset_analysis,
    help="MSE abaixo deste valor → NORMAL",
)

st.sidebar.slider(
    "Threshold Borderline (MSE)",
    min_value=0.000, max_value=0.100, value=0.020, step=0.001,
    format="%.3f",
    key="threshold_borderline",
    on_change=reset_analysis,
    help="MSE entre Normal e este valor → BORDERLINE",
)

st.sidebar.checkbox(
    "Simular latência",
    value=True,
    key="simulate_latency",
)

st.sidebar.markdown("---")

if st.sidebar.button("Limpar Cache"):
    st.cache_data.clear()
    st.sidebar.success("Cache limpo com sucesso.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.info(
    "Triagem de pneumonia via VAE — erro de reconstrução como sinal de anomalia. "
    "Sempre consulte um médico para diagnóstico definitivo."
)


# ==========================================================
# TÍTULO & EMPTY STATE
# ==========================================================
st.title("VAE PneumoniaMNIST — Triagem de Pneumonia e Geração de Imagens")

uploaded = st.file_uploader(
    "Envie uma imagem de raio-X para análise (PNG/JPG)",
    type=["png", "jpg", "jpeg"],
)

if not uploaded:
    st.info("Envie uma imagem de raio-X para iniciar a análise.")
    st.stop()


# ==========================================================
# BOTÃO COMO GATILHO (AÇÃO, NÃO ESTADO)
# ==========================================================
if st.button("🔍 Executar Triagem", type="primary"):
    st.session_state.analysis_ran = True
    st.session_state.run_file_key = uploaded.name + str(uploaded.size)


# ==========================================================
# EXECUÇÃO CONTROLADA PELO ESTADO
# ==========================================================
if st.session_state.analysis_ran:

    file_key = st.session_state.get("run_file_key", "")

    # --------------------------------------------------------
    # LOADING STATE / LATÊNCIA — só na primeira execução do arquivo
    # --------------------------------------------------------
    if st.session_state.get("last_file_key") != file_key:
        if st.session_state.simulate_latency:
            with st.spinner("Pré-processando imagem..."):
                time.sleep(0.5)
            with st.spinner("Codificando no espaço latente..."):
                time.sleep(0.5)
            with st.spinner("Reconstruindo imagem..."):
                bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    bar.progress(i + 1)
            st.toast("Análise concluída.")
        st.session_state.last_file_key = file_key

    # --------------------------------------------------------
    # PROCESSAMENTO
    # --------------------------------------------------------
    image = Image.open(io.BytesIO(uploaded.read()))
    x = preprocess_image(image)
    recon = vae(x, training=False).numpy()
    mse = compute_reconstruction_error(x, recon)

    classification, description, color = classify_pneumonia(
        mse,
        st.session_state.threshold_normal,
        st.session_state.threshold_borderline,
    )
    confidence_percent = max(0, int((1 - mse) * 100)) if mse < 1 else 0

    # Atualiza resultado e histórico apenas se for nova execução
    if st.session_state.last_result is None or st.session_state.last_result.get("file_key") != file_key:
        st.session_state.last_result = {
            "x": x, "recon": recon, "mse": mse,
            "classification": classification,
            "confidence": confidence_percent,
            "file_key": file_key,
        }
        new_row = pd.DataFrame([{
            "Execução":       len(st.session_state.history) + 1,
            "Classificação":  classification,
            "Erro MSE":       round(mse, 6),
            "Confiança (%)":  confidence_percent,
        }])
        st.session_state.history_df = pd.concat(
            [st.session_state.history_df, new_row], ignore_index=True
        )
        st.session_state.history.append({
            "classification": classification,
            "mse": mse,
            "confidence": confidence_percent,
        })

    # ==========================================================
    # TABS DE RESULTADOS
    # ==========================================================
    tab_triagem, tab_geracao, tab_dados, tab_monitor, tab_sobre = st.tabs([
        "🔍 Triagem & Validação Humana",
        "🎨 Gerar Novas Imagens",
        "📊 Dados & Histórico",
        "📈 Monitoramento",
        "ℹ️ Sobre o Modelo",
    ])

    # ==========================================================
    # TAB 1 — TRIAGEM & VALIDAÇÃO HUMANA
    # ==========================================================
    with tab_triagem:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Imagem Original")
            st.image(x[0].squeeze(), clamp=True,width="stretch")
        with col2:
            st.subheader("Reconstrução VAE")
            st.image(recon[0].squeeze(), clamp=True,width="stretch")

        st.markdown("---")
        st.subheader("📊 Resultado da Triagem")

        # KPIs com delta em relação à execução anterior
        prev_mse = st.session_state.history[-2]["mse"] if len(st.session_state.history) >= 2 else None
        delta_mse = f"{(mse - prev_mse):+.6f}" if prev_mse is not None else None

        m1, m2, m3 = st.columns(3)
        m1.metric("Erro de Reconstrução (MSE)", f"{mse:.6f}", delta=delta_mse, delta_color="inverse")
        m2.metric("Classificação", classification)
        m3.metric("Confiança estimada", f"{confidence_percent}%")

        st.progress(confidence_percent)

        # Alerta contextual
        if color == "green":
            st.success(f"✅ {classification} — {description}")
        elif color == "orange":
            st.warning(f"⚠️ {classification} — {description}")
        else:
            st.error(f"🚨 {classification} — {description}")

        # Banner colorido HTML
        st.markdown(f"""
        <div style="padding:1rem; border-radius:0.5rem;
                    background-color:{color}20; border-left:4px solid {color}; margin-top:0.5rem;">
            <h4 style="color:{color}; margin:0;">{classification}</h4>
            <p style="margin:0.5rem 0 0 0;">{description}</p>
        </div>
        """, unsafe_allow_html=True)

        st.caption("⚠️ **Importante:** Este é apenas um auxiliar de triagem. Sempre consulte um médico para diagnóstico definitivo.")

        st.markdown("---")

        # Human-in-the-loop
        st.subheader("Validação Humana")
        fc1, fc2 = st.columns(2)
        with fc1:
            if st.button("✅ Classificação correta"):
                st.session_state.feedback_log.append(
                    {"classification": classification, "mse": mse, "correct": True}
                )
                st.success("Feedback registrado.")
        with fc2:
            if st.button("❌ Classificação incorreta"):
                st.session_state.feedback_log.append(
                    {"classification": classification, "mse": mse, "correct": False}
                )
                st.error("Feedback registrado.")

    # ==========================================================
    # TAB 2 — GERAÇÃO DE IMAGENS
    # ==========================================================
    with tab_geracao:
        st.header("🎨 Geração de Novas Imagens de Raio-X")
        st.markdown("Gere novas imagens sintéticas de raio-X usando o espaço latente aprendido pelo VAE.")

        col1, col2 = st.columns([2, 1])
        with col1:
            num_images = st.slider("Número de imagens a gerar", 1, 8, 4)
            if st.button("🔄 Gerar Novas Imagens", type="primary"):
                with st.spinner("Gerando imagens..."):
                    st.session_state.generated_images = generate_new_images(vae, num_images)
                    st.session_state.num_generated = num_images
        with col2:
            st.markdown("""
            **Controles:**
            - Ajuste o número de imagens
            - Clique em gerar para criar novas
            - As imagens são amostradas do espaço latente normal
            """)

        if st.session_state.generated_images is not None:
            st.subheader("Imagens Geradas")
            n = st.session_state.num_generated
            cols = st.columns(n)
            for i, col in enumerate(cols):
                with col:
                    st.image(
                        st.session_state.generated_images[i].squeeze(),
                        clamp=True,
                        caption=f"Imagem {i + 1}",
                        width="stretch",
                    )

    # ==========================================================
    # TAB 3 — DADOS & HISTÓRICO
    # ==========================================================
    with tab_dados:
        st.subheader("Histórico de Análises")
        st.caption(
            "Tabela interativa: ordene, redimensione e inspecione. "
            "A coluna *Confiança* é exibida como barra visual."
        )

        if not st.session_state.history_df.empty:
            st.dataframe(
                st.session_state.history_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Confiança (%)": st.column_config.ProgressColumn(
                        "Confiança",
                        help="Confiança estimada pelo modelo",
                        min_value=0,
                        max_value=100,
                        format="%d%%",
                    ),
                    "Erro MSE": st.column_config.NumberColumn("Erro MSE", format="%.6f"),
                },
            )

            st.markdown("#### Estatísticas descritivas")
            st.caption("Antes de confiar no gráfico, inspecione o dado bruto.")
            st.dataframe(
                st.session_state.history_df[["Erro MSE", "Confiança (%)"]].describe().round(6),
                use_container_width=True,
            )

            st.markdown("---")
            st.markdown("#### Erro de Reconstrução por Análise")
            fig_hist = px.bar(
                st.session_state.history_df,
                x="Execução",
                y="Erro MSE",
                color="Classificação",
                color_discrete_map={
                    "NORMAL": "green",
                    "BORDERLINE": "orange",
                    "POSSÍVEL PNEUMONIA": "red",
                },
                title="Erro MSE por execução",
                height=320,
            )
            fig_hist.add_hline(
                y=st.session_state.threshold_normal,
                line_dash="dash", line_color="green",
                annotation_text="Threshold Normal",
            )
            fig_hist.add_hline(
                y=st.session_state.threshold_borderline,
                line_dash="dash", line_color="orange",
                annotation_text="Threshold Borderline",
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # ==========================================================
    # TAB 4 — MONITORAMENTO
    # ==========================================================
    with tab_monitor:
        st.subheader("Monitoramento do Sistema")

        total_fb = len(st.session_state.feedback_log)
        if total_fb > 0:
            correct = sum(1 for f in st.session_state.feedback_log if f["correct"])
            accuracy = correct / total_fb

            mon1, mon2, mon3 = st.columns(3)
            mon1.metric("Feedbacks recebidos", total_fb)
            mon2.metric("Acertos validados", correct)
            mon3.metric("Acurácia percebida", f"{int(accuracy * 100)}%")

            if accuracy < 0.7:
                st.warning("⚠️ Possível degradação do modelo detectada.")
        else:
            st.info("Ainda não há feedback suficiente para monitoramento.")

        st.markdown("---")

        # Gráfico nativo: evolução do MSE
        if len(st.session_state.history) > 1:
            st.markdown("#### Evolução do Erro de Reconstrução (MSE)")
            st.caption("Gráfico nativo do Streamlit (`st.line_chart`): ideal para prototipação rápida de séries temporais.")
            mse_series = pd.DataFrame(
                {"Erro MSE": [h["mse"] for h in st.session_state.history]},
                index=range(1, len(st.session_state.history) + 1),
            )
            mse_series.index.name = "Execução"
            st.line_chart(mse_series)

        # Altair: distribuição de classificações
        if len(st.session_state.history) >= 2:
            st.markdown("#### Distribuição de Classificações")
            st.caption("Gráfico Altair com gramática declarativa: mapeia categoria → cor → contagem de forma explícita.")
            hist_df = pd.DataFrame(st.session_state.history)
            class_counts = hist_df.groupby("classification").size().reset_index(name="Contagem")

            chart_classes = (
                alt.Chart(class_counts)
                .mark_bar()
                .encode(
                    x=alt.X("classification:N", title="Classificação"),
                    y=alt.Y("Contagem:Q", title="Número de triagens"),
                    color=alt.Color(
                        "classification:N",
                        scale=alt.Scale(
                            domain=["NORMAL", "BORDERLINE", "POSSÍVEL PNEUMONIA"],
                            range=["green", "orange", "red"],
                        ),
                        legend=None,
                    ),
                    tooltip=["classification", "Contagem"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart_classes, use_container_width=True)

        # Plotly scatter histórico
        if len(st.session_state.history) >= 3:
            st.markdown("#### Scatter: Erro MSE × Execução por Classificação")
            st.caption("Plotly `px.scatter`: interativo, com hover nativo e legenda clicável para filtrar classificações.")
            scatter_df = st.session_state.history_df.copy()
            fig_scatter = px.scatter(
                scatter_df,
                x="Execução",
                y="Erro MSE",
                color="Classificação",
                color_discrete_map={
                    "NORMAL": "green",
                    "BORDERLINE": "orange",
                    "POSSÍVEL PNEUMONIA": "red",
                },
                hover_data=["Confiança (%)"],
                title="Histórico de triagens",
                height=320,
            )
            fig_scatter.add_hline(
                y=st.session_state.threshold_normal,
                line_dash="dash", line_color="green",
                annotation_text=f"Threshold Normal ({st.session_state.threshold_normal:.3f})",
            )
            fig_scatter.add_hline(
                y=st.session_state.threshold_borderline,
                line_dash="dash", line_color="orange",
                annotation_text=f"Threshold Borderline ({st.session_state.threshold_borderline:.3f})",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # Filtro interativo com botão
        if not st.session_state.history_df.empty:
            st.markdown("---")
            st.markdown("#### Filtrar histórico por Erro MSE máximo")
            st.caption("O filtro só é aplicado ao clicar em **Aplicar**, evitando reprocessamento a cada ajuste do slider.")

            max_mse_filter = st.slider(
                "MSE máximo",
                min_value=0.000, max_value=0.100, value=0.050, step=0.001,
                format="%.3f",
                key="mse_filter",
            )

            if st.button("Aplicar filtro"):
                st.session_state["filtered_history"] = st.session_state.history_df[
                    st.session_state.history_df["Erro MSE"] <= max_mse_filter
                ]

            if "filtered_history" in st.session_state:
                st.dataframe(
                    st.session_state["filtered_history"],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Confiança (%)": st.column_config.ProgressColumn(
                            "Confiança (%)", min_value=0, max_value=100, format="%d%%"
                        ),
                        "Erro MSE": st.column_config.NumberColumn("Erro MSE", format="%.6f"),
                    },
                )

    # ==========================================================
    # TAB 5 — SOBRE O MODELO
    # ==========================================================
    with tab_sobre:
        st.header("ℹ️ Sobre o Modelo VAE")
        st.markdown("""
        ### Arquitetura do Modelo

        **Encoder:**
        Conv2D(32) → Conv2D(64) → Flatten → Dense(128) → Espaço Latente (z_mean, z_log_var, z)

        **Decoder:**
        Dense(7×7×64) → Reshape → Conv2DTranspose(64) → Conv2DTranspose(32) → Output(sigmoid)

        ### Como Funciona a Triagem

        1. **Imagens Normais:** O VAE foi treinado em imagens normais — erro de reconstrução baixo.
        2. **Imagens com Pneumonia:** Padrões diferentes do aprendido → maior erro de reconstrução.
        3. **Thresholds configuráveis** na barra lateral:
           - MSE < Threshold Normal → **NORMAL**
           - Threshold Normal ≤ MSE < Threshold Borderline → **BORDERLINE**
           - MSE ≥ Threshold Borderline → **POSSÍVEL PNEUMONIA**

        ### Limitações

        - Treinado apenas em PneumoniaMNIST (imagens 28×28 grayscale)
        - Não substitui diagnóstico médico profissional
        - Sensibilidade depende da qualidade e resolução da imagem enviada
        """)

        st.markdown("---")
        st.subheader("Estatísticas do Modelo")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Parâmetros Encoder", f"{vae.encoder.count_params():,}")
            st.metric("Parâmetros Decoder", f"{vae.decoder.count_params():,}")
        with col2:
            st.metric("Total de Parâmetros", f"{vae.count_params():,}")
            st.metric("Dimensão Latente", vae.encoder.output_shape[0][-1])

else:
    st.info("Configure os parâmetros na barra lateral e clique em **🔍 Executar Triagem**.")

# ==========================================================
# FOOTER
# ==========================================================
st.markdown("---")
st.caption(
    "🔬 **Modelo VAE para Triagem de Pneumonia** | "
    "Desenvolvido com TensorFlow e Streamlit | "
    "Sempre consulte um médico para diagnóstico definitivo."
)