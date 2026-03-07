import streamlit as st
from state.session import init_session
from ui.sidebar import render_sidebar

# 1. Configuração Global
st.set_page_config(page_title="AI News Analyzer", layout="wide")

# 2. Estado
init_session()

# 3. UI (Sidebar e Navegação)
page_id = render_sidebar()

# 4. Roteamento de Features
if page_id == "analysis":
    from features.news_analysis.page import render
elif page_id == "history":
    from features.history.page import render
else:
    from features.settings.page import render

render()