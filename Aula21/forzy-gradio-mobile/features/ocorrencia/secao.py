# =============================================================================
# features/ocorrencia/secao.py — Registro de ocorrência (human-in-the-loop)
#
# O Gradio não tem diálogo modal nativo. A seção fica escondida e aparece
# quando o operador toca em "Registrar ocorrência"; no nível avançado, o CSS
# a transforma numa folha que sobe da base da tela (bottom sheet).
#
# Digitar de luva é caro: as ocorrências comuns são opções de um toque e o
# texto livre é opcional.
# =============================================================================

from datetime import datetime

import gradio as gr

TIPOS_COMUNS = ["Ruído anormal", "Aquecimento", "Vibração", "Vazamento", "Cheiro de queimado", "Outro"]


def criar_secao(botao_abrir: gr.Button, entrada_tag: gr.components.Component) -> gr.Column:
    """Cria a seção, liga o botão que a abre e devolve a coluna criada."""
    with gr.Column(visible=False, elem_classes="fz-folha") as folha:
        gr.Markdown("**Registrar ocorrência**")
        tipos = gr.CheckboxGroup(TIPOS_COMUNS, label="O que você observou?")
        detalhe = gr.Textbox(label="Detalhes (opcional)", lines=3,
                             placeholder="Ex.: ruído metálico só sob carga máxima")
        with gr.Row(elem_classes="fz-acoes"):
            cancelar = gr.Button("Cancelar", size="lg")
            registrar = gr.Button("Registrar", variant="primary", size="lg")

    def _registrar(tag: str, marcados: list[str], texto: str):
        if not marcados and not (texto or "").strip():
            gr.Warning("Escolha ao menos um tipo ou descreva a ocorrência.")
            return gr.skip(), gr.skip(), gr.skip()
        # Em produção: POST /v1/ocorrencias no back-end.
        gr.Info(f"Ocorrência registrada para {tag} às {datetime.now():%H:%M}.", title="Registrado")
        return gr.Column(visible=False), [], ""

    botao_abrir.click(lambda: gr.Column(visible=True), outputs=folha)
    cancelar.click(lambda: (gr.Column(visible=False), [], ""), outputs=[folha, tipos, detalhe])
    registrar.click(_registrar, inputs=[entrada_tag, tipos, detalhe], outputs=[folha, tipos, detalhe])
    return folha
