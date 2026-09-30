# =============================================================================
# ui/sidebar.py — Componente de navegação lateral
#
# Componente de UI puro: não conhece pipelines nem providers. A única coisa
# que ele faz é desenhar os botões e pedir a troca de página ao app_state.
#
# Cadastro Técnico não aparece no menu — é acessado a partir da tela de
# Equipamentos, em modo "novo" ou "edicao".
# =============================================================================

import streamlit as st

from state import app_state

# (chave da página, rótulo do botão)
_ITENS = [
    ("equipamentos", "🏠  Equipamentos"),
    ("dados", "📡  Dados de Sensores"),
    ("dashboard", "📊  Dashboard"),
]


def criar_sidebar() -> None:
    """Desenha o menu lateral e destaca o item da página ativa."""
    with st.sidebar:
        st.markdown("## ⚙️ Forzy")
        st.caption("Digital Twin · Motores")
        st.divider()
        st.markdown("**Navegação**")

        atual = app_state.pagina_atual()

        for chave, rotulo in _ITENS:
            # A página de Cadastro é filha de Equipamentos: mantém o menu destacado.
            ativo = chave == atual or (chave == "equipamentos" and atual == "cadastro")

            if st.button(
                rotulo,
                key=f"nav_{chave}",
                width="stretch",
                type="primary" if ativo else "secondary",
            ):
                app_state.ir_para(chave)

        st.divider()
        st.caption("Sprint 2 — Visualização Operacional")
