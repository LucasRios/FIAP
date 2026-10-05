# =============================================================================
# state/app_state.py — Estado compartilhado entre as telas (Gradio)
#
# Uma página não troca de tela sozinha: ela escreve um PEDIDO DE NAVEGAÇÃO
# em state.navegar, e o roteador do app.py reage a esse pedido (troca a aba,
# carrega o motor, abre a ficha). É o mesmo desenho da versão anterior, em
# que state.pagina_atual.change() mostrava a coluna certa.
#
# O pedido carrega um contador: pedir duas vezes a mesma tela ainda é uma
# mudança de valor, e o .change() dispara de novo.
# =============================================================================

import itertools

import gradio as gr

DESTINOS = ("motores", "cadastro", "painel", "sensores")
_contador = itertools.count(1)


def pedido(destino: str, tag: str = "", modo: str = "") -> dict:
    """Monta um pedido de navegação. Destinos desconhecidos viram 'motores'."""
    return {"destino": destino if destino in DESTINOS else "motores",
            "tag": tag, "modo": modo, "n": next(_contador)}


def pedido_da_url(parametros: dict) -> dict:
    """
    Deep link: ?pagina=painel&tag=MTR-007 (o QR code colado no motor).

    Os valores vêm da URL, logo do usuário: só são aceitos se forem um destino
    conhecido e uma TAG no formato MTR-000.
    """
    destino = parametros.get("pagina", "motores")
    tag = str(parametros.get("tag", "")).strip().upper()
    tag = tag if re_tag(tag) else ""
    modo = "edicao" if destino == "cadastro" and tag else ""
    return pedido(destino, tag, modo)


def re_tag(tag: str) -> bool:
    return tag.startswith("MTR-") and tag[4:].isdigit() and len(tag) == 7


class AppState:
    """Contêiner dos gr.State. Instanciar UMA VEZ dentro do gr.Blocks()."""

    def __init__(self):
        self.navegar = gr.State(pedido("motores"))
