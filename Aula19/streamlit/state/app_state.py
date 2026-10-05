# =============================================================================
# state/app_state.py — Estado compartilhado entre as páginas
#
# Na versão Gradio esta camada era uma classe com objetos gr.State, e cada
# mudança disparava um evento .change(). No Streamlit o estado vive em
# st.session_state (um dicionário por aba do navegador) e não dispara evento
# nenhum: qualquer interação reexecuta o script inteiro, de cima para baixo,
# e as páginas simplesmente leem o valor atual.
#
# Este módulo existe para que nenhuma feature escreva chaves soltas em
# st.session_state — todas passam por funções com nome.
# =============================================================================

import streamlit as st

# Valores iniciais de cada chave, aplicados uma única vez por sessão.
_PADROES = {
    "pagina": "equipamentos",   # página visível: equipamentos | cadastro | dados | dashboard
    "tag_selecionada": "",      # TAG em foco, carregada ao abrir Sensores ou Dashboard
    "modo_cadastro": "novo",    # novo (formulário em branco) | edicao (pré-preenchido)
}


def inicializar() -> None:
    """Garante que todas as chaves existam. Chamada uma vez, no app.py."""
    for chave, valor in _PADROES.items():
        st.session_state.setdefault(chave, valor)


def pagina_atual() -> str:
    return st.session_state["pagina"]


def ir_para(pagina: str, tag: str | None = None, modo: str | None = None) -> None:
    """
    Navega para outra página e, opcionalmente, define a TAG e o modo do cadastro.

    Depois de atualizar o estado, st.rerun() reexecuta o script imediatamente,
    para que a interface já apareça na página nova — sem esperar o próximo clique.
    """
    st.session_state["pagina"] = pagina
    if tag is not None:
        st.session_state["tag_selecionada"] = tag
    if modo is not None:
        st.session_state["modo_cadastro"] = modo
    st.rerun()


def tag_selecionada() -> str:
    return st.session_state["tag_selecionada"]


def modo_cadastro() -> str:
    return st.session_state["modo_cadastro"]
