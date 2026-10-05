# =============================================================================
# state/app_state.py — Estado compartilhado entre as páginas
#
# O estado vive em st.session_state e é espelhado na URL (?pagina=...&tag=...).
# O espelhamento serve a um caso de uso típico de campo: um QR code colado no
# motor abre o app direto no painel daquele motor.
#
#   https://forzy.streamlit.app/?pagina=dashboard&tag=MTR-007
#
# A URL é lida UMA vez, quando a sessão começa. Depois disso, quem manda é o
# session_state, e a URL só é atualizada para continuar compartilhável e para
# sobreviver a um recarregamento da página.
# =============================================================================

import streamlit as st

PAGINAS = ("equipamentos", "cadastro", "dados", "dashboard")

_PADROES = {
    "pagina": "equipamentos",   # página visível
    "tag_selecionada": "",      # TAG em foco nas telas de detalhe
    "modo_cadastro": "novo",    # novo | edicao
}


def inicializar() -> None:
    """
    Garante as chaves do estado e aplica o deep link na primeira execução.

    Valores vindos da URL são entrada do usuário: só são aceitos se forem uma
    página conhecida e uma TAG no formato esperado.
    """
    if "pagina" in st.session_state:
        return

    for chave, valor in _PADROES.items():
        st.session_state[chave] = valor

    pagina = st.query_params.get("pagina", "")
    tag = st.query_params.get("tag", "").strip().upper()

    if pagina in PAGINAS:
        st.session_state["pagina"] = pagina
    if tag.startswith("MTR-") and tag[4:].isdigit():
        st.session_state["tag_selecionada"] = tag
        if pagina == "cadastro":
            st.session_state["modo_cadastro"] = "edicao"


def pagina_atual() -> str:
    return st.session_state["pagina"]


def tag_selecionada() -> str:
    return st.session_state["tag_selecionada"]


def modo_cadastro() -> str:
    return st.session_state["modo_cadastro"]


def ir_para(pagina: str, tag: str | None = None, modo: str | None = None) -> None:
    """Troca de página, atualiza a URL e reexecuta o script imediatamente."""
    st.session_state["pagina"] = pagina
    if tag is not None:
        st.session_state["tag_selecionada"] = tag
    if modo is not None:
        st.session_state["modo_cadastro"] = modo

    parametros = {"pagina": pagina, "tag": st.session_state["tag_selecionada"]}
    st.query_params.from_dict({k: v for k, v in parametros.items() if v})
    st.rerun()
