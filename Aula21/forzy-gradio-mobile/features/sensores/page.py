# =============================================================================
# features/sensores/page.py — Dados brutos dos sensores (Gradio)
#
# Tela secundária no celular: mesmos cards do painel (consistência),
# histórico completo sob demanda e registro de ocorrência.
# =============================================================================

import tempfile

import gradio as gr

import pipelines.sensor_pipeline as pipeline
from features.ocorrencia.secao import criar_secao
from ui.componentes import GRANDEZAS as CARDS_GRANDEZAS


def _carregar(tag: str | None):
    if not tag:
        return CARDS_GRANDEZAS.valor(None), "", None
    dados = pipeline.grandezas_atuais(tag)
    if not dados:
        gr.Warning(f"Não foi possível obter a leitura de {tag}.")
        return CARDS_GRANDEZAS.valor(None), "", None
    return CARDS_GRANDEZAS.valor(dados["itens"]), f"Leitura das {dados['hora']}", pipeline.historico_para_tabela(tag)


def _csv(tag: str | None) -> str | None:
    """Gera o CSV do histórico num arquivo temporário para o botão de download."""
    if not tag:
        return None
    arquivo = tempfile.NamedTemporaryFile(prefix=f"historico_{tag}_", suffix=".csv", delete=False)
    pipeline.historico_para_tabela(tag).to_csv(arquivo.name, index=False)
    return arquivo.name


def criar_pagina() -> dict:
    gr.Markdown("Leituras em unidades físicas · limites ISO 10816")
    motor = gr.Dropdown([], label="Motor", filterable=True, value=None)
    hora = gr.Markdown()
    grandezas = CARDS_GRANDEZAS.criar()

    with gr.Accordion("Histórico completo (48 leituras)", open=False):
        tabela = gr.Dataframe(headers=pipeline.COLUNAS_HISTORICO, interactive=False, max_height=320)
        baixar = gr.DownloadButton("Baixar CSV", size="lg")

    with gr.Row(elem_classes="fz-acoes"):
        abrir_ocorrencia = gr.Button("Registrar ocorrência", variant="primary", size="lg")
    criar_secao(abrir_ocorrencia, motor)

    motor.change(_carregar, inputs=motor, outputs=[grandezas, hora, tabela])
    motor.change(_csv, inputs=motor, outputs=baixar)
    return {"motor": motor}
