# =============================================================================
# features/equipamentos/page.py — Lista de motores (tela inicial)
#
# Antes: tabela de 8 colunas (só 4 visíveis no celular) + caixa de seleção
# de 20 px + botões de ação abaixo da tabela, longe do item selecionado.
# Agora: busca + filtro por toque + um card por motor, com as ações dentro
# do próprio card. A página só ORQUESTRA: os componentes vêm de ui/.
# =============================================================================

import streamlit as st

import pipelines.cadastro_pipeline as pipeline
import providers.api_provider as api_provider
from state import app_state
from ui import componentes as ui
from ui.tokens import STATUS_OPERACIONAL


def render() -> None:
    ui.titulo_tela("Motores", "Toque em um motor para ver o painel ou a ficha técnica.")

    # type="search": no celular, o teclado ganha a tecla "Buscar" no lugar de "Enter".
    busca = st.text_input(
        "Buscar", placeholder="TAG, modelo ou local", type="search",
        label_visibility="collapsed", key="busca_equipamentos",
    )
    status = st.pills(
        "Status", list(STATUS_OPERACIONAL), selection_mode="single",
        label_visibility="collapsed", key="filtro_status",
    )

    itens = pipeline.listar_equipamentos(busca, status)

    erro = api_provider.ultimo_erro()
    if erro:
        ui.estado_erro(f"{erro} Tente novamente em alguns segundos.")
        return
    if not itens:
        ui.estado_vazio("Nenhum motor encontrado com esse filtro.", ":material/search_off:")
        return

    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        st.caption(f"{len(itens)} motor(es)")
        if st.button("Novo", icon=":material/add:", key="novo_equipamento"):
            app_state.ir_para("cadastro", tag="", modo="novo")

    for eq in itens:
        acao = ui.cartao_equipamento(eq)
        if acao == "painel":
            app_state.ir_para("dashboard", tag=eq["tag"])
        elif acao == "ficha":
            app_state.ir_para("cadastro", tag=eq["tag"], modo="edicao")
