# =============================================================================
# app.py — Ponto de entrada do Forzy (Streamlit, versão mobile-first)
#
# Camadas:
#   ui/tokens.py        design tokens: a única fonte de verdade visual
#   ui/componentes.py   componentes do design system
#   ui/navegacao.py     barra superior e navegação principal
#   ui/estilo.py        camada opcional de CSS (nível avançado)
#   state/app_state.py  estado compartilhado + deep link pela URL
#   features/*/page.py  telas: só orquestram componentes
#   pipelines/          dados prontos para a tela
#   providers/          única porta de saída para a API
#
# O tema (cores, tipografia, raios) vem de .streamlit/config.toml, gerado a
# partir dos tokens com `python -m ui.tokens > .streamlit/config.toml`.
# =============================================================================

import os

import streamlit as st

# layout="centered": coluna única e confortável no celular; no desktop, uma
# coluna de leitura no centro. É a decisão "mobile-first" em uma palavra.
st.set_page_config(page_title="Forzy · Digital Twin", page_icon="⚙️",
                   layout="centered", initial_sidebar_state="collapsed")

import features.cadastro.page as cadastro_page          # noqa: E402
import features.dashboard.page as dashboard_page        # noqa: E402
import features.equipamentos.page as equipamentos_page  # noqa: E402
import features.sensores.page as sensores_page          # noqa: E402
import providers.api_provider as api_provider           # noqa: E402
from state import app_state                             # noqa: E402
from ui.estilo import aplicar_estilo                    # noqa: E402
from ui.navegacao import barra_navegacao, barra_superior  # noqa: E402

PAGINAS = {
    "equipamentos": equipamentos_page.render,
    "cadastro": cadastro_page.render,
    "dados": sensores_page.render,
    "dashboard": dashboard_page.render,
}

# Nível avançado (CSS) ligado por padrão; FORZY_CSS=0 mostra só o nível nativo.
if os.getenv("FORZY_CSS", "1") == "1":
    aplicar_estilo(st.context.theme.type or "light")

app_state.inicializar()

if not st.session_state.get("_api_acordada"):
    with st.spinner("Acordando a API… o plano gratuito hiberna após alguns minutos sem acesso."):
        api_provider.acordar_api()

# Feedback não crítico vindo da execução anterior (salvar, registrar) vira toast:
# some sozinho e não empurra o conteúdo. Erros nunca vão para cá.
aviso = st.session_state.pop("_aviso_global", None)
if aviso:
    st.toast(aviso, icon=":material/check_circle:")

barra_superior()
barra_navegacao()

PAGINAS[app_state.pagina_atual()]()
