# =============================================================================
# app.py — Ponto de entrada da aplicação (Streamlit)
#
# Estrutura (a mesma da versão Gradio):
#   ui/sidebar.py       ← componente visual do menu, sem lógica
#   state/app_state.py  ← estado compartilhado entre páginas
#   features/*/page.py  ← conteúdo de cada página
#   pipelines/          ← formatação dos dados para a tela
#   providers/          ← única porta de saída para o back-end
#
# O modelo de execução muda: no Gradio, eventos atualizavam componentes
# específicos. No Streamlit, qualquer interação reexecuta ESTE arquivo
# inteiro, de cima para baixo, e a tela é redesenhada. Por isso o roteador
# abaixo é um simples if/elif — não há eventos para registrar.
# =============================================================================

import streamlit as st

# set_page_config precisa ser o primeiro comando Streamlit do script.
st.set_page_config(
    page_title="Forzy · Digital Twin",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import features.cadastro.page as cadastro_page          # noqa: E402
import features.dashboard.page as dashboard_page        # noqa: E402
import features.equipamentos.page as equipamentos_page  # noqa: E402
import features.sensores.page as sensores_page          # noqa: E402
import providers.api_provider as api_provider           # noqa: E402
from state import app_state                             # noqa: E402
from ui.sidebar import criar_sidebar                    # noqa: E402

PAGINAS = {
    "equipamentos": equipamentos_page.render,
    "cadastro": cadastro_page.render,
    "dados": sensores_page.render,
    "dashboard": dashboard_page.render,
}

app_state.inicializar()

# A API pode estar hibernada no tier gratuito. Acordá-la antes de desenhar
# qualquer tela evita que a primeira visita do dia mostre uma página vazia.
if not st.session_state.get("_api_acordada"):
    with st.spinner("Acordando a API… (o plano gratuito hiberna após alguns minutos sem acesso)"):
        api_provider.acordar_api()

criar_sidebar()

# Roteador: desenha apenas a página ativa.
PAGINAS[app_state.pagina_atual()]()
