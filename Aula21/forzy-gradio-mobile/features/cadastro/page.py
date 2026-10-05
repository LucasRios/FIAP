# =============================================================================
# features/cadastro/page.py — Ficha técnica e formulário (Gradio)
#
# Fica DENTRO da aba Motores, numa coluna que substitui a lista quando um
# motor é aberto — a navegação "lista → detalhe → voltar" de um app nativo.
# Formulário em coluna única; pares curtos lado a lado com min_width, que o
# Gradio empilha sozinho quando não cabem.
# =============================================================================

import gradio as gr

import pipelines.cadastro_pipeline as pipeline
import providers.api_provider as api_provider
from state.app_state import AppState, pedido, re_tag
from ui.componentes import PARES

FABRICANTES = ["WEG", "Siemens", "ABB", "Nidec", "Voges", "Outro"]
CLASSES_ISOLAMENTO = ["A", "B", "F", "H"]
IPS = ["IP21", "IP44", "IP54", "IP55", "IP65", "IP66"]
TENSOES = [220, 380, 440, 480, 690]
STATUS = ["Operacional", "Em Manutenção", "Desligado"]
CAMPOS = ["tag", "modelo", "fabricante", "potencia_cv", "tensao_v", "corrente_nominal_a", "fator_potencia",
          "rotacao_rpm", "peso_kg", "classe_isolamento", "ip", "local", "status"]
_VAZIO = {"tag": "", "modelo": "", "fabricante": "WEG", "potencia_cv": 1.0, "tensao_v": 380,
          "corrente_nominal_a": 1.0, "fator_potencia": 0.86, "rotacao_rpm": 1760, "peso_kg": 1.0,
          "classe_isolamento": "F", "ip": "IP55", "local": "", "status": "Operacional"}


def criar_pagina(state: AppState) -> dict:
    with gr.Row(elem_classes="fz-acoes"):
        voltar = gr.Button("← Motores", size="lg", variant="secondary", min_width=140, scale=0)
    titulo = gr.Markdown("### Novo motor")
    visao = gr.Radio([("Ficha", "ficha"), ("Editar", "edicao")], value="ficha", show_label=False, container=False)

    with gr.Column() as col_ficha:
        ficha = PARES.criar()

    with gr.Column(visible=False) as col_form:
        gr.Markdown("**Identificação**")
        f = {
            "tag": gr.Textbox(label="TAG", placeholder="MTR-021"),
            "modelo": gr.Textbox(label="Modelo", placeholder="W22 160L"),
            "fabricante": gr.Dropdown(FABRICANTES, label="Fabricante"),
        }
        gr.Markdown("**Elétrica**")
        with gr.Row():
            f["potencia_cv"] = gr.Number(label="Potência (cv)", minimum=0.5, min_width=150)
            f["tensao_v"] = gr.Dropdown(TENSOES, label="Tensão (V)", min_width=150)
        with gr.Row():
            f["corrente_nominal_a"] = gr.Number(label="Corrente (A)", minimum=0.1, min_width=150)
            f["fator_potencia"] = gr.Number(label="Fator de potência", minimum=0.6, maximum=1.0, step=0.01, min_width=150)
        gr.Markdown("**Mecânica e construção**")
        with gr.Row():
            f["rotacao_rpm"] = gr.Number(label="Rotação (RPM)", minimum=500, precision=0, min_width=150)
            f["peso_kg"] = gr.Number(label="Peso (kg)", minimum=1, min_width=150)
        with gr.Row():
            f["classe_isolamento"] = gr.Dropdown(CLASSES_ISOLAMENTO, label="Isolamento", min_width=150)
            f["ip"] = gr.Dropdown(IPS, label="Proteção (IP)", min_width=150)
        gr.Markdown("**Localização e estado**")
        f["local"] = gr.Textbox(label="Local", placeholder="Planta A — Linha 1")
        f["status"] = gr.Dropdown(STATUS, label="Status operacional")
        with gr.Row(elem_classes="fz-acoes fz-salvar"):
            salvar = gr.Button("Salvar", variant="primary", size="lg")

    campos = [f[c] for c in CAMPOS]

    # ── Funções chamadas pelo roteador e pelos eventos locais ─────────────
    def _visoes(v: str):
        return gr.Column(visible=v == "ficha"), gr.Column(visible=v == "edicao")

    def abrir(tag: str, modo: str) -> list:
        """Atualizações para abrir a tela: título, visão, colunas, ficha e campos."""
        if modo == "novo" or not tag:
            return [gr.Markdown("### Novo motor"), gr.Radio(value="edicao", visible=False),
                    gr.Column(visible=False), gr.Column(visible=True), PARES.valor(None),
                    *[_VAZIO[c] for c in CAMPOS]]
        eq = pipeline.carregar_equipamento(tag) or {}
        base = {**_VAZIO, **eq}
        return [gr.Markdown(f"### Motor {tag}"), gr.Radio(value="ficha", visible=True),
                gr.Column(visible=True), gr.Column(visible=False), PARES.valor(pipeline.ficha_tecnica(tag)),
                *[base[c] for c in CAMPOS]]

    def _salvar(*valores):
        dados = dict(zip(CAMPOS, valores))
        tag = (dados["tag"] or "").strip().upper()
        if not re_tag(tag):
            gr.Warning("Use o formato MTR-000 na TAG, por exemplo MTR-021.")
            return gr.skip()
        if not (dados["modelo"] or "").strip():
            gr.Warning("Informe o modelo do motor.")
            return gr.skip()
        sucesso, mensagem = pipeline.salvar_equipamento(**dados)
        if not sucesso:
            gr.Warning(mensagem)
            return gr.skip()
        api_provider.limpar_cache()
        gr.Info(mensagem, title="Salvo")
        return pedido("cadastro", tag, "edicao")

    visao.change(_visoes, inputs=visao, outputs=[col_ficha, col_form])
    salvar.click(_salvar, inputs=campos, outputs=state.navegar)
    voltar.click(lambda: pedido("motores"), outputs=state.navegar)

    return {"abrir": abrir, "saidas_abrir": [titulo, visao, col_ficha, col_form, ficha, *campos]}
