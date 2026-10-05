# =============================================================================
# features/equipamentos/page.py — Lista de motores (Gradio)
#
# Antes: gr.Dataframe de 8 colunas + seleção de linha + botões abaixo da
# tabela. Agora: busca, filtro por status e um card por motor, gerados com
# @gr.render — cada card tem os próprios botões, com eventos próprios.
#
# Os botões não trocam de tela: escrevem um pedido em state.navegar.
# =============================================================================

import gradio as gr

import pipelines.cadastro_pipeline as pipeline
from state.app_state import AppState, pedido
from ui.componentes import EQUIPAMENTO
from ui.tokens import STATUS_OPERACIONAL


def criar_pagina(state: AppState) -> dict:
    with gr.Row(equal_height=True):
        busca = gr.Textbox(placeholder="TAG, modelo ou local", show_label=False, scale=4,
                           min_width=180, container=False)
        novo = gr.Button("Novo", size="lg", scale=1, min_width=96)
    status = gr.Radio(list(STATUS_OPERACIONAL), show_label=False, value=None, container=False)
    recarregar = gr.State(0)  # incrementado pelo app.load para buscar a lista fresca

    @gr.render(inputs=[busca, status, recarregar])
    def _cards(texto, filtro, _):
        itens = pipeline.listar_equipamentos(texto or "", filtro)
        if not itens:
            gr.Markdown("Nenhum motor encontrado com esse filtro.")
            return
        gr.Markdown(f"{len(itens)} motor(es)")
        for eq in itens:
            with gr.Group(elem_classes="fz-card"):
                EQUIPAMENTO.criar(value=EQUIPAMENTO.valor(eq), key=f"cab_{eq['tag']}")
                with gr.Row(elem_classes="fz-acoes"):
                    painel = gr.Button("Painel", variant="primary", size="lg", min_width=120, key=f"p_{eq['tag']}")
                    ficha = gr.Button("Ficha", size="lg", min_width=120, key=f"f_{eq['tag']}")
            # tag=eq["tag"] congela o valor do laço em cada função
            painel.click(lambda tag=eq["tag"]: pedido("painel", tag), outputs=state.navegar)
            ficha.click(lambda tag=eq["tag"]: pedido("cadastro", tag, "edicao"), outputs=state.navegar)

    novo.click(lambda: pedido("cadastro", "", "novo"), outputs=state.navegar)
    return {"recarregar": recarregar}
