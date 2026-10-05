# =============================================================================
# features/dashboard/page.py — Dashboard Operacional
#
# Navegação em cascata Planta → Área → Equipamento.
#
# Na versão Gradio, cada nível precisava de um evento .change() que
# reescrevia as opções do dropdown seguinte. No Streamlit a cascata é
# consequência natural do modelo de execução: o script roda de cima para
# baixo, então quando a linha do selectbox de Áreas é executada, a planta
# escolhida logo acima já está na variável.
# =============================================================================

import streamlit as st

import pipelines.dashboard_pipeline as pipeline
import providers.api_provider as api_provider
from state import app_state


def render() -> None:
    st.markdown("## 📊 Dashboard Operacional")
    st.caption(
        "Selecione a localização do ativo para monitorar seu estado em tempo real. "
        "🟢 Normal · 🟡 Aviso · 🔴 Crítico"
    )

    plantas = api_provider.listar_plantas()
    if not plantas:
        st.error("Não foi possível carregar as plantas. Verifique se a API está no ar.")
        return

    # Quem chega aqui pela tela de Equipamentos traz uma TAG: descobrimos
    # onde ela está instalada e posicionamos os três seletores.
    tag_externa = app_state.tag_selecionada()
    planta_ini, area_ini = api_provider.buscar_localizacao(tag_externa) if tag_externa else ("", "")

    st.markdown("### 🗺️ Localização do Ativo")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    planta = c1.selectbox(
        "Planta", plantas,
        index=plantas.index(planta_ini) if planta_ini in plantas else 0,
        help="Instalação industrial",
    )

    areas = api_provider.listar_areas(planta)
    area = c2.selectbox(
        "Área", areas,
        index=areas.index(area_ini) if area_ini in areas else 0,
        help="Setor ou linha de produção",
    ) if areas else None

    equipamentos = api_provider.listar_equipamentos(planta, area) if area else []
    tag = c3.selectbox(
        "Equipamento (TAG)", equipamentos,
        index=equipamentos.index(tag_externa) if tag_externa in equipamentos else 0,
        help="TAG de identificação do motor",
    ) if equipamentos else None

    c4.markdown("&nbsp;", unsafe_allow_html=True)  # alinha o botão com os seletores
    if c4.button("🔄 Atualizar Leitura", type="primary", width="stretch"):
        api_provider.limpar_cache()
        st.rerun()

    if not tag:
        st.info("Selecione uma planta, uma área e um equipamento.")
        return

    st.divider()

    # ── Telemetria em tempo real ────────────────────────────────────────────
    st.markdown("### 📡 Telemetria em Tempo Real")

    dados = pipeline.telemetria(tag)
    if not dados:
        st.warning(f"Equipamento {tag} não encontrado no cadastro.")
        return

    st.markdown(f"**{dados['titulo']}** · Status: _{dados['status']}_")
    st.caption(f"Leitura em {dados['timestamp']}")

    colunas = st.columns(len(dados["metricas"]))
    for coluna, (rotulo, valor, icone) in zip(colunas, dados["metricas"]):
        coluna.metric(f"{icone} {rotulo}", valor)

    st.divider()

    # ── Histórico ───────────────────────────────────────────────────────────
    # Uma leitura pontual não revela tendência. Temperatura subindo aos poucos
    # ao longo de horas pode indicar falha no sistema de resfriamento.
    st.markdown("### 📈 Histórico das Últimas 24h")
    st.caption(
        "Intervalo de 30 min entre amostras (48 pontos). "
        "Linhas tracejadas: limites de Aviso (laranja) e Crítico (vermelho)."
    )

    fig = pipeline.grafico_historico(tag)
    if fig is None:
        st.info("Sem histórico disponível para esta TAG.")
    else:
        st.plotly_chart(fig, width="stretch")

    st.divider()

    # ── Placa de identificação ──────────────────────────────────────────────
    # Na Sprint 3 esta seção exibirá a foto real da placa, lida por Visão
    # Computacional. Por ora, os dados vêm do cadastro técnico.
    st.markdown("### 🏷️ Placa de Identificação")
    st.caption("Simulação — na Sprint 3 será a foto real, lida por Visão Computacional.")

    placa = pipeline.placa_texto(tag)
    if placa:
        st.code(placa, language=None)
