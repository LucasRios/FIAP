# =============================================================================
# features/sensores/page.py — Dados brutos dos sensores
#
# Diferença de comportamento em relação à versão Gradio: lá era preciso
# clicar em "Leitura Atual" para buscar os dados. Aqui, escolher a TAG no
# selectbox já reexecuta o script e carrega tudo — o clique extra some.
# O botão de atualizar continua existindo para forçar dados novos,
# descartando o que está memorizado no cache.
# =============================================================================

from datetime import datetime

import streamlit as st

import pipelines.sensor_pipeline as pipeline
import providers.api_provider as api_provider
from state import app_state


def render() -> None:
    st.markdown("## 📡 Dados Brutos dos Sensores")
    st.caption(
        "Leituras convertidas para unidades físicas (V, A, °C, mm/s, RPM). "
        "Severidade: 🟢 Normal · 🟡 Aviso · 🔴 Crítico — limites baseados na ISO 10816."
    )

    tags = api_provider.tags_disponiveis()
    if not tags:
        st.error("Não foi possível carregar as TAGs. Verifique se a API está no ar.")
        return

    # A TAG que veio da tela de Equipamentos já aparece selecionada.
    tag_externa = app_state.tag_selecionada()
    indice = tags.index(tag_externa) if tag_externa in tags else 0

    col_tag, col_btn = st.columns([3, 1])
    tag = col_tag.selectbox("Equipamento (TAG)", tags, index=indice)

    col_btn.markdown("&nbsp;", unsafe_allow_html=True)  # alinha o botão com o campo
    if col_btn.button("🔄 Atualizar", width="stretch"):
        api_provider.limpar_cache()
        st.rerun()

    st.divider()

    # ── Leitura atual ───────────────────────────────────────────────────────
    st.markdown("### Leitura em Tempo Real")

    cards = pipeline.leitura_para_cards(tag)
    if not cards:
        st.warning(f"Não foi possível obter a leitura de {tag}.")
    else:
        st.caption(f"Amostra de {cards['timestamp']}")
        colunas = st.columns(len(cards["metricas"]))
        for coluna, (rotulo, valor, icone) in zip(colunas, cards["metricas"]):
            coluna.metric(f"{icone} {rotulo}", valor)

    st.divider()

    # ── Histórico ───────────────────────────────────────────────────────────
    st.markdown("### Histórico de Leituras (últimas 24h)")
    st.caption("Intervalo de 30 minutos entre amostras — 48 pontos no total.")

    historico = pipeline.historico_para_tabela(tag)
    if historico.empty:
        st.info("Sem histórico disponível para esta TAG.")
    else:
        st.dataframe(historico, hide_index=True, width="stretch", height=320)

        # Um DataFrame em mãos permite oferecer o download sem nenhum esforço extra.
        st.download_button(
            "⬇️ Baixar histórico (CSV)",
            data=historico.to_csv(index=False).encode("utf-8"),
            file_name=f"historico_{tag}.csv",
            mime="text/csv",
        )

    st.divider()

    # ── Human-in-the-loop ───────────────────────────────────────────────────
    # O operador registra o que os sensores sozinhos não capturam. Esses
    # registros alimentarão o dataset de anomalias na Sprint 3.
    st.markdown("### 🖊️ Registrar Ocorrência")
    st.caption(
        "Registre comportamentos anômalos observados no campo. "
        "Seu registro alimentará o modelo de detecção de anomalias na Sprint 3."
    )

    with st.form("form_ocorrencia", clear_on_submit=True):
        descricao = st.text_input(
            "Descrição",
            placeholder="Ex.: ruído metálico intermitente sob carga máxima...",
        )
        registrar = st.form_submit_button("📝 Registrar")

    if registrar:
        if not descricao.strip():
            st.error("Descreva a ocorrência antes de registrar.")
        else:
            # Em produção: POST /v1/ocorrencias no back-end.
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Ocorrência registrada para {tag} em {ts}.")
