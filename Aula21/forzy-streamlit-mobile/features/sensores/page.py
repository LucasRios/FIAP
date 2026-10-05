# =============================================================================
# features/sensores/page.py — Dados brutos dos sensores
#
# No celular, esta tela é secundária: o painel já mostra o essencial. Aqui
# ficam os dados para quem quer conferir números — leitura atual nos mesmos
# cards do painel (consistência), histórico completo sob demanda e o
# registro de ocorrência.
# =============================================================================

import streamlit as st

import pipelines.sensor_pipeline as pipeline
import providers.api_provider as api_provider
from features.ocorrencia.dialogo import dialogo_ocorrencia
from state import app_state
from ui import componentes as ui


def render() -> None:
    ui.titulo_tela("Sensores", "Leituras em unidades físicas · limites ISO 10816")

    tags = api_provider.tags_disponiveis()
    if not tags:
        ui.estado_erro("Não foi possível carregar os motores. Verifique se a API está no ar.")
        return

    atual = app_state.tag_selecionada()
    tag = st.selectbox("Motor", tags, index=tags.index(atual) if atual in tags else 0, key=f"sensor_{atual}")
    if tag != atual:
        st.session_state["tag_selecionada"] = tag
        st.query_params["tag"] = tag

    dados = pipeline.grandezas_atuais(tag)
    if not dados:
        ui.estado_erro(f"Não foi possível obter a leitura de {tag}.")
        return

    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        st.caption(f"Leitura das {dados['hora']}")
        if st.button("Atualizar", icon=":material/refresh:", key="atualizar_sensores"):
            api_provider.limpar_cache()
            st.rerun()

    ui.grade_grandezas(dados["itens"])

    ui.espaco("sm")
    with st.expander("Histórico completo (48 leituras)", icon=":material/table_rows:"):
        historico = pipeline.historico_para_tabela(tag)
        st.dataframe(historico, hide_index=True, width="stretch", height=280)
        st.download_button(
            "Baixar CSV", data=historico.to_csv(index=False).encode("utf-8"),
            file_name=f"historico_{tag}.csv", mime="text/csv",
            icon=":material/download:", width="stretch",
        )

    with st.container(key="acoes_sensores"):
        if st.button("Registrar ocorrência", icon=":material/edit_note:", type="primary", width="stretch"):
            dialogo_ocorrencia(tag)
