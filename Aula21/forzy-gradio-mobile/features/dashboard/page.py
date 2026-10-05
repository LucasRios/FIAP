# =============================================================================
# features/dashboard/page.py — Painel de um motor (Gradio)
#
# Mesma ordem de leitura da versão Streamlit, "o status primeiro":
# escolha do motor → resumo → ações → grandezas → gráfico → placa.
# Esta página só ORQUESTRA: dados vêm das pipelines (as mesmas do
# Streamlit, sem nenhuma alteração) e o desenho vem de ui/componentes.py.
# =============================================================================

import gradio as gr

import pipelines.dashboard_pipeline as pipeline
import providers.api_provider as api_provider
from features.ocorrencia.secao import criar_secao
from pipelines.formatacao import GRANDEZAS
from ui.componentes import GRANDEZAS as CARDS_GRANDEZAS
from ui.componentes import PARES, RESUMO


def opcoes_motores(tags: list[str] | None = None) -> list[tuple[str, str]]:
    """(rótulo, valor) do seletor. Um único GET traz o local de todos — sem N+1."""
    locais = {e["tag"]: e["local"] for e in api_provider.listar_todos()}
    return [(f"{t} · {locais.get(t, '')}", t) for t in (tags if tags is not None else api_provider.tags_disponiveis())]


def _carregar(tag: str | None):
    """Preenche o painel inteiro para um motor."""
    vazio = (RESUMO.valor(None), CARDS_GRANDEZAS.valor(None), gr.Radio(value=None), None, PARES.valor(None))
    if not tag:
        return vazio
    p = pipeline.painel(tag)
    if not p:
        gr.Warning(f"Não foi possível obter os dados de {tag}.")
        return vazio
    return (
        RESUMO.valor(p),
        CARDS_GRANDEZAS.valor(p["grandezas"]),
        gr.Radio(value=p["grandeza_destaque"]),
        pipeline.grafico_grandeza(tag, p["grandeza_destaque"]),
        PARES.valor(pipeline.placa(tag)),
    )


def criar_pagina() -> dict:
    """Monta a tela e devolve os componentes que o roteador precisa alcançar."""
    with gr.Accordion("Filtrar por planta e área", open=False):
        planta = gr.Radio([], label="Planta")
        area = gr.Radio([], label="Área")

    motor = gr.Dropdown([], label="Motor", filterable=True, value=None)
    resumo = RESUMO.criar()

    with gr.Row(elem_classes="fz-acoes"):
        abrir_ocorrencia = gr.Button("Registrar ocorrência", variant="primary", size="lg", min_width=220)
        atualizar = gr.Button("Atualizar", size="lg", min_width=120)
    criar_secao(abrir_ocorrencia, motor)

    gr.Markdown("**Grandezas agora**")
    grandezas = CARDS_GRANDEZAS.criar()

    gr.Markdown("**Últimas 24 horas**")
    escolha = gr.Radio([(g["nome"], c) for c, g in GRANDEZAS.items()], show_label=False, value=None)
    grafico = gr.Plot(show_label=False)

    with gr.Accordion("Placa de identificação", open=False):
        placa = PARES.criar()

    # ── Eventos ────────────────────────────────────────────────────────────
    saidas = [resumo, grandezas, escolha, grafico, placa]

    def _ao_escolher_planta(p):
        areas = api_provider.listar_areas(p)
        tags = [t for a in areas for t in api_provider.listar_equipamentos(p, a)]
        return gr.Radio(choices=areas, value=None), gr.Dropdown(choices=opcoes_motores(tags))

    def _ao_escolher_area(p, a):
        if not a:
            return gr.skip()
        return gr.Dropdown(choices=opcoes_motores(api_provider.listar_equipamentos(p, a)))

    planta.change(_ao_escolher_planta, inputs=planta, outputs=[area, motor])
    area.change(_ao_escolher_area, inputs=[planta, area], outputs=motor)
    motor.change(_carregar, inputs=motor, outputs=saidas)
    escolha.input(lambda t, c: pipeline.grafico_grandeza(t, c) if t and c else None,
                  inputs=[motor, escolha], outputs=grafico)

    def _atualizar(tag):
        api_provider.limpar_cache()
        return _carregar(tag)

    atualizar.click(_atualizar, inputs=motor, outputs=saidas)

    return {"motor": motor, "planta": planta}
