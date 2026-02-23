import pandas as pd
import streamlit as st
import random
import time
import numpy as np
import plotly.express as px
import altair as alt
from datetime import datetime

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(page_title="AI UX Demo", layout="wide")


# ==============================================================
# SECRETS MANAGEMENT
# Nunca hardcode credenciais. Use st.secrets em produção.
# Aqui simulamos o padrão com fallback seguro para demo local.
# Em produção: st.secrets["model_api_key"]
# ==============================================================
APP_CONFIG = {
    "model_api_key": st.secrets.get("model_api_key", "demo-key-local"),
    "db_url":        st.secrets.get("db_url",        "sqlite:///:memory:"),
    "api_ttl":       int(st.secrets.get("api_ttl", 60)),   # TTL em segundos
}


# ==========================================================
# region INICIALIZAÇÃO DE ESTADO (centralizado — Aula 05)
#
# Aula 05: Centralize todo o estado em session_state.
# Isso evita recalcular filtros e dados pesados a cada rerun.
# ==========================================================
_DEFAULTS = {
    "history":          [],
    "last_result":      None,
    "feedback_log":     [],
    "analysis_ran":     False,
    "config_version":   0,
    "run_seed":         42,
    "last_seed":        None,
    "filtered_history": None,
    "history_df": pd.DataFrame(
        columns=["Execução", "Classe", "Confiança (%)", "Modelo", "Threshold", "Timestamp"]
    ),
    # Estado de conectividade
    "api_data_loaded":  False,
    "api_payload":      None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v
# endregion


# ==========================================================
# AULA 05 — CAMADA DE RECURSOS (cache_resource)
#
# cache_resource → objetos pesados, conexões, modelos.
# Instanciado UMA ÚNICA VEZ. Compartilhado entre reruns.
# Não serializa → mantém o objeto vivo na memória.
# ==========================================================
class SimulatedModel:
    """
    Representa um modelo de IA pesado.
    Em produção seria: transformers, sklearn, torch, etc.
    """
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.loaded_at  = datetime.now().strftime("%H:%M:%S")
        # Simula custo de carregamento
        time.sleep(0.1)

    def predict(self, threshold: float, seed: int) -> tuple[str, float, dict]:
        rng        = random.Random(seed)
        base_score = rng.uniform(0.4, 0.95)
        if self.model_type == "Avançado":
            base_score += 0.05
        score = min(base_score, 0.99)
        label = "Cachorro" if score >= threshold else "Gato"
        explanation = {
            "Formato das orelhas": round(rng.uniform(0.1, 0.4), 2),
            "Textura do pelo":     round(rng.uniform(0.1, 0.4), 2),
            "Formato do focinho":  round(rng.uniform(0.1, 0.4), 2),
        }
        return label, score, explanation


@st.cache_resource
def get_model(model_type: str) -> SimulatedModel:
    """
    AULA 05 — cache_resource
    Carrega e mantém o modelo em memória entre reruns.
    A instância é compartilhada: não é recriada a cada interação.
    Ideal para: modelos de ML, conexões de banco, clientes de API.
    """
    return SimulatedModel(model_type)


# Simula uma conexão de banco (padrão cache_resource — Aula 05)
@st.cache_resource
def get_db_connection(db_url: str):
    """
    AULA 05 — cache_resource para conexão de banco.
    A conexão é criada uma vez e reutilizada.
    Em produção: create_engine(db_url) com SQLAlchemy.
    """
    return {"url": db_url, "connected_at": datetime.now().strftime("%H:%M:%S")}


# ==========================================================
# AULA 05 — CAMADA DE DADOS (cache_data)
#
# cache_data → dados transformados, queries, respostas de API.
# Serializa o resultado. Seguro para múltiplos usuários.
# ==========================================================

@st.cache_data(ttl=APP_CONFIG["api_ttl"], show_spinner=False)
def fetch_simulated_api(model_type: str, api_key: str) -> dict:
    """
    AULA 05 — cache_data com TTL.
    Simula chamada a uma API externa (ex: OpenAI, serviço de metadados).

    TTL = APP_CONFIG["api_ttl"] segundos.
    Após esse período, o cache expira e a API é consultada novamente.
    Isso equilibra performance e atualização dos dados.

    Dependência explícita: model_type e api_key são parâmetros —
    nunca use variáveis externas sem declará-las como argumento.
    """
    time.sleep(0.05)  # simula latência de rede
    return {
        "model_version":  "v2.1.0" if model_type == "Avançado" else "v1.3.0",
        "last_updated":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy_report": round(random.uniform(0.80, 0.97), 3),
        "requests_today":  random.randint(100, 5000),
    }


@st.cache_data(show_spinner=False)
def run_inference(model_type: str, threshold: float, seed: int) -> tuple:
    """
    AULA 05 — Camada de processamento cacheada.
    Separa processamento de visualização.

    Todas as dependências (model_type, threshold, seed) são
    parâmetros explícitos → o hash é previsível e correto.
    Sem dependências invisíveis.
    """
    model = get_model(model_type)   # cache_resource: não recarrega
    return model.predict(threshold, seed)


@st.cache_data(show_spinner=False)
def build_explanation_df(explanation: dict) -> pd.DataFrame:
    """
    AULA 05 — Transformação cacheada.
    Resultado é imutável: sempre use .copy() ao consumir.
    """
    return pd.DataFrame(
        [{"Feature": k, "Peso": v} for k, v in explanation.items()]
    )


@st.cache_data(show_spinner=False)
def compute_history_stats(history_tuple: tuple) -> pd.DataFrame:
    """
    AULA 05 — Separe computação pesada de visualização.
    Recebe tupla (hashável) para que o cache funcione corretamente.
    """
    if not history_tuple:
        return pd.DataFrame()
    df = pd.DataFrame(list(history_tuple))
    return df.describe().round(2)


# ==========================================================
# CALLBACKS
# ==========================================================
def reset_analysis():
    st.session_state.analysis_ran = False
    st.session_state.last_result  = None
    st.session_state.config_version += 1
    st.toast("Configuração alterada. Execute novamente.")


def clear_all_cache():
    """
    AULA 05 — Invalidação manual de cache.
    st.cache_data.clear() limpa todos os resultados cacheados.
    Útil para reset administrativo ou debug.
    """
    st.cache_data.clear()
    st.cache_resource.clear()
    reset_analysis()
    st.toast("🗑️ Cache limpo manualmente.", icon="🗑️")


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

# ---- AULA 05 — Invalidação manual de cache na sidebar ----
st.sidebar.markdown("### 🛠️ Administração de Cache")
st.sidebar.caption(
    f"TTL da API: **{APP_CONFIG['api_ttl']}s** · "
    f"Chave: `{APP_CONFIG['model_api_key'][:8]}…`"
)
if st.sidebar.button("🗑️ Limpar todo o cache", use_container_width=True):
    clear_all_cache()

st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.info(
    "Classificador simulado com explicabilidade, "
    "human-in-the-loop e performance (Aulas 04 + 05)."
)


# ==========================================================
# TÍTULO E UPLOAD
# ==========================================================
st.title("Classificador de Imagem (Simulado)")

uploaded = st.file_uploader("Envie uma imagem", type=["png", "jpg", "jpeg"])

if not uploaded:
    st.info("Envie uma imagem para iniciar a análise.")
    st.stop()


# ==========================================================
# AULA 05 — LAZY LOADING DA API
#
# Carregue dados externos apenas quando necessário.
# Evita custo de rede e latência no carregamento inicial.
# ==========================================================
if not st.session_state.api_data_loaded:
    st.caption("ℹ️ Metadados do modelo não carregados ainda.")
    if st.button("🌐 Carregar metadados do modelo (API)"):
        with st.spinner("Consultando API de metadados..."):
            st.session_state.api_payload      = fetch_simulated_api(
                st.session_state.model_type, APP_CONFIG["model_api_key"]
            )
            st.session_state.api_data_loaded  = True
        st.toast("Metadados carregados.")
        st.rerun()
else:
    api = st.session_state.api_payload
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Versão do modelo",   api["model_version"])
    mc2.metric("Acurácia reportada", f"{api['accuracy_report']*100:.1f}%")
    mc3.metric("Requisições hoje",   api["requests_today"])
    mc4.metric("Última atualização", api["last_updated"].split(" ")[1])
    st.caption(
        f"⏱️ Dados com cache TTL de **{APP_CONFIG['api_ttl']}s**. "
        "Após esse período, a API será consultada automaticamente."
    )

st.markdown("---")


# ==========================================================
# BOTÃO COMO GATILHO
# ==========================================================
if st.button("▶️ Executar Análise"):
    st.session_state.analysis_ran = True
    st.session_state.run_seed     = int(time.time() * 1000) % 100_000


# ==========================================================
# EXECUÇÃO CONTROLADA PELO ESTADO
# ==========================================================
if st.session_state.analysis_ran:

    seed = st.session_state.run_seed

    # Spinners apenas no primeiro run do seed atual
    if st.session_state.last_seed != seed:
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

    # --------------------------------------------------------
    # AULA 05 — Camada de processamento separada da visualização.
    # run_inference é cacheada: mesmo seed+config → retorna do cache.
    # O modelo (cache_resource) não é recarregado.
    # --------------------------------------------------------
    label, score, explanation = run_inference(
        st.session_state.model_type,
        st.session_state.threshold,
        seed,
    )
    confidence_percent = int(score * 100)

    # Atualiza histórico apenas para seeds novos
    if st.session_state.last_result is None or st.session_state.last_result.get("seed") != seed:
        st.session_state.last_result = {
            "label": label, "score": score,
            "explanation": explanation, "seed": seed,
        }
        new_row = pd.DataFrame([{
            "Execução":      len(st.session_state.history) + 1,
            "Classe":        label,
            "Confiança (%)": confidence_percent,
            "Modelo":        st.session_state.model_type,
            "Threshold":     st.session_state.threshold,
            "Timestamp":     datetime.now().strftime("%H:%M:%S"),
        }])
        # AULA 05 — .copy() antes de manipular DataFrame cacheado
        st.session_state.history_df = pd.concat(
            [st.session_state.history_df.copy(), new_row], ignore_index=True
        )
        st.session_state.history.append({"label": label, "score": score})

    # ==========================================================
    # TABS DE RESULTADOS
    # ==========================================================
    tab_pred, tab_dados, tab_monitor, tab_perf = st.tabs([
        "Predição & Validação Humana",
        "Dados & Explicabilidade",
        "Monitoramento & Histórico",
        "⚡ Performance & Cache",
    ])

    # ==========================================================
    # TAB 1 — PREDIÇÃO
    # ==========================================================
    with tab_pred:
        st.subheader("Resultado da Classificação")

        prev       = st.session_state.history[-2]["score"] if len(st.session_state.history) >= 2 else None
        delta_val  = f"{(score - prev) * 100:+.1f}%" if prev else None

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
    # TAB 2 — DADOS & EXPLICABILIDADE (Aula 04 mantida)
    # ==========================================================
    with tab_dados:
        st.subheader("Inspeção dos Dados de Saída")

        st.markdown("#### Histórico de execuções")
        st.caption(
            "Tabela interativa com `st.dataframe` + `column_config`. "
            "A coluna *Confiança* é exibida como barra visual. "
            "A coluna *Timestamp* rastreia o momento de cada run."
        )

        if not st.session_state.history_df.empty:
            # AULA 05 — .copy() antes de exibir objeto cacheado
            display_df = st.session_state.history_df.copy()

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Confiança (%)": st.column_config.ProgressColumn(
                        "Confiança (%)",
                        help="Score de confiança do modelo",
                        min_value=0, max_value=100, format="%d%%",
                    ),
                    "Threshold": st.column_config.NumberColumn(
                        "Threshold", format="%.2f"
                    ),
                    "Timestamp": st.column_config.TextColumn("Horário"),
                },
            )

            st.markdown("#### Estatísticas descritivas")
            # AULA 05 — computação pesada isolada em função cacheada
            history_tuple = tuple(
                (h["label"], h["score"]) for h in st.session_state.history
            )
            stats_df = compute_history_stats(history_tuple)
            if not stats_df.empty:
                st.dataframe(stats_df, use_container_width=True)

        st.markdown("---")

        st.subheader("Explicabilidade Local")

        # AULA 05 — build_explanation_df é cacheada.
        # .copy() obrigatório antes de qualquer mutação.
        exp_df = build_explanation_df(explanation).copy()

        fig_exp = px.bar(
            exp_df,
            x="Peso", y="Feature", orientation="h",
            color="Peso", color_continuous_scale="Blues",
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

        st.markdown("**Resumo estático da explicabilidade**")
        st.table(
            exp_df.set_index("Feature")
                  .rename(columns={"Peso": "Peso relativo"})
        )

    # ==========================================================
    # TAB 3 — MONITORAMENTO & HISTÓRICO (Aula 04 mantida)
    # ==========================================================
    with tab_monitor:
        st.subheader("Monitoramento do Sistema")

        total_fb = len(st.session_state.feedback_log)
        if total_fb > 0:
            correct  = sum(1 for f in st.session_state.feedback_log if f["correct"])
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

        if len(st.session_state.history) > 1:
            st.markdown("#### Evolução da confiança por execução")
            conf_series = pd.DataFrame(
                {"Confiança (%)": [int(h["score"] * 100) for h in st.session_state.history]},
                index=range(1, len(st.session_state.history) + 1),
            )
            conf_series.index.name = "Execução"
            st.line_chart(conf_series)

        if len(st.session_state.history) >= 2:
            st.markdown("#### Distribuição de classes previstas")
            hist_df      = pd.DataFrame(st.session_state.history)
            class_counts = (
                hist_df.groupby("label").size().reset_index(name="Contagem")
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

        if len(st.session_state.history) >= 3:
            st.markdown("#### Scatter: confiança × execução por classe")
            scatter_df = st.session_state.history_df.copy()   # AULA 05 — .copy()
            fig_scatter = px.scatter(
                scatter_df,
                x="Execução", y="Confiança (%)",
                color="Classe", symbol="Modelo",
                hover_data=["Threshold", "Timestamp"],
                title="Histórico de predições",
                height=320,
            )
            fig_scatter.add_hline(
                y=int(st.session_state.threshold * 100),
                line_dash="dash", line_color="gray",
                annotation_text=f"Threshold ({int(st.session_state.threshold*100)}%)",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # ---- Filtro com botão (padrão Aula 04 + estado centralizado Aula 05) ----
        if not st.session_state.history_df.empty:
            st.markdown("---")
            st.markdown("#### Filtrar histórico por confiança mínima")
            st.caption(
                "Slider + botão: o filtro pesado só roda ao clicar **Aplicar**, "
                "evitando reprocessamento a cada arrasto."
            )
            min_conf = st.slider("Confiança mínima (%)", 0, 100, 50, key="min_conf_filter")
            if st.button("Aplicar filtro"):
                # AULA 05 — .copy() antes de filtrar objeto do session_state
                base = st.session_state.history_df.copy()
                st.session_state.filtered_history = base[
                    base["Confiança (%)"] >= min_conf
                ]

            if st.session_state.filtered_history is not None:
                st.dataframe(
                    st.session_state.filtered_history,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Confiança (%)": st.column_config.ProgressColumn(
                            "Confiança (%)", min_value=0, max_value=100, format="%d%%"
                        )
                    },
                )

    # ==========================================================
    # TAB 4 — PERFORMANCE & CACHE (Aula 05 — exclusiva)
    # ==========================================================
    with tab_perf:
        st.subheader("⚡ Diagnóstico de Performance e Cache")

        st.markdown(
            """
            Esta aba documenta e demonstra, em tempo real, os padrões de performance
            da Aula 05 aplicados neste app.
            """
        )

        # ---- Status do modelo em cache ----
        st.markdown("### 🧠 Modelo em cache (`cache_resource`)")
        model_instance = get_model(st.session_state.model_type)

        col_r1, col_r2 = st.columns(2)
        col_r1.metric("Tipo de modelo", model_instance.model_type)
        col_r2.metric("Carregado em", model_instance.loaded_at)

        st.caption(
            "`get_model()` usa `@st.cache_resource`: o objeto é instanciado **uma única vez** "
            "e reutilizado em todos os reruns. Troque o modelo no sidebar para ver um novo "
            "horário de carregamento."
        )

        # ---- Status da conexão de banco ----
        st.markdown("### 🗄️ Conexão de banco (`cache_resource`)")
        db_conn = get_db_connection(APP_CONFIG["db_url"])
        db1, db2 = st.columns(2)
        db1.metric("URL",          db_conn["url"])
        db2.metric("Conectado em", db_conn["connected_at"])
        st.caption(
            "Em produção: `create_engine(st.secrets['db_url'])`. "
            "A conexão é criada uma vez e jamais recriada por rerun."
        )

        st.markdown("---")

        # ---- Status da API cacheada com TTL ----
        st.markdown(f"### 🌐 API externa (`cache_data` com TTL={APP_CONFIG['api_ttl']}s)")
        if st.session_state.api_data_loaded:
            api = st.session_state.api_payload
            ttl_info = pd.DataFrame([{
                "Parâmetro":   "TTL configurado",
                "Valor":       f"{APP_CONFIG['api_ttl']} segundos",
                "Significado": "Após esse tempo, o cache expira e a API é consultada novamente.",
            }, {
                "Parâmetro":   "Última consulta real",
                "Valor":       api["last_updated"],
                "Significado": "Enquanto o TTL não expirar, este valor é reutilizado.",
            }, {
                "Parâmetro":   "Custo evitado",
                "Valor":       "N chamadas → 1",
                "Significado": "Múltiplos reruns reutilizam o mesmo resultado sem nova latência.",
            }])
            st.table(ttl_info.set_index("Parâmetro"))
        else:
            st.info("Carregue os metadados do modelo (botão acima) para ver o status da API.")

        st.markdown("---")

        # ---- Arquitetura em camadas ----
        st.markdown("### 🏗️ Arquitetura em camadas")
        layers = pd.DataFrame([{
            "Camada":         "Recursos (`cache_resource`)",
            "Função":         "get_model(), get_db_connection()",
            "O que armazena": "Instância do objeto (modelo, conexão)",
            "TTL":            "Indefinido (até reinício da sessão)",
        }, {
            "Camada":         "Dados (`cache_data`)",
            "Função":         "run_inference(), fetch_simulated_api(), build_explanation_df()",
            "O que armazena": "Resultado serializado (DataFrame, dict, tuple)",
            "TTL":            f"{APP_CONFIG['api_ttl']}s (API) / sem TTL (inferência)",
        }, {
            "Camada":         "Estado (`session_state`)",
            "Função":         "history, feedback_log, filtered_history…",
            "O que armazena": "Estado entre reruns do usuário atual",
            "TTL":            "Duração da sessão do navegador",
        }, {
            "Camada":         "Visualização",
            "Função":         "st.plotly_chart, st.altair_chart, st.dataframe…",
            "O que armazena": "Nada — apenas consome as camadas acima",
            "TTL":            "Reconstruída a cada rerun",
        }])
        st.dataframe(layers.set_index("Camada"), use_container_width=True)

        st.markdown("---")

        # ---- Checklist de performance ----
        st.markdown("### ✅ Checklist de App Performático (Aula 05)")
        checklist = {
            "Dados cacheados com `cache_data`":                       True,
            "Recursos cacheados com `cache_resource`":                True,
            "`.copy()` sempre que objeto cacheado é mutado":          True,
            "Dependências explícitas como parâmetros (sem vars ext)": True,
            "TTL configurado para APIs externas":                     True,
            "Invalidação manual disponível (`cache_data.clear()`)":   True,
            "Estado centralizado em `session_state`":                 True,
            "Slider + botão para filtros pesados":                    True,
            "Lazy loading para dados externos":                       True,
            "Credenciais em `st.secrets` (não hardcoded)":            True,
            "Camadas separadas: dados / processamento / visualização": True,
        }
        check_df = pd.DataFrame([
            {"Item": k, "Status": "✅" if v else "❌"}
            for k, v in checklist.items()
        ])
        st.table(check_df.set_index("Item"))

else:
    st.info("Configure os parâmetros e clique em **▶️ Executar Análise**.")