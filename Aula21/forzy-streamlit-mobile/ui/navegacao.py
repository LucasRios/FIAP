# =============================================================================
# ui/navegacao.py — Barra superior e navegação principal
#
# Substitui o ui/sidebar.py. No celular, a sidebar vira um menu escondido
# atrás de um ícone — e quando abre, cobre a tela inteira. Três destinos de
# primeiro nível pedem uma barra de navegação SEMPRE visível, o padrão que
# Material e Apple recomendam para 3 a 5 destinos.
#
# No nível nativo, a barra fica no topo. O CSS opcional (ui/estilo.py) a
# move para a base da tela, na zona do polegar — sem tocar neste arquivo.
# =============================================================================

import streamlit as st

from state import app_state

# chave da página -> rótulo com ícone Material (curto: cabe em 360 px)
DESTINOS = {
    "equipamentos": ":material/precision_manufacturing: Motores",
    "dashboard": ":material/monitoring: Painel",
    "dados": ":material/sensors: Sensores",
}


def barra_superior() -> None:
    """Identidade do app numa linha só: o conteúdo começa logo abaixo."""
    with st.container(horizontal=True, vertical_alignment="center", key="barra_superior"):
        st.markdown("**⚙️ Forzy**")
        st.caption("Digital Twin · Motores")


def barra_navegacao() -> None:
    """
    Navegação de primeiro nível como controle segmentado.

    A página de Cadastro é filha de Motores: enquanto ela está aberta,
    "Motores" continua destacado, como acontece num app nativo.
    """
    atual = app_state.pagina_atual()
    destacado = "equipamentos" if atual == "cadastro" else atual

    # A chave muda junto com a página para o controle renascer com o novo
    # valor padrão quando a navegação acontece por código (ir_para).
    with st.container(key="nav_principal"):
        escolha = st.segmented_control(
            "Navegação",
            options=list(DESTINOS),
            format_func=DESTINOS.get,
            default=destacado,
            required=True,
            key=f"nav_{destacado}",
            label_visibility="collapsed",
            width="stretch",
        )
    if escolha and escolha != destacado:
        app_state.ir_para(escolha)
