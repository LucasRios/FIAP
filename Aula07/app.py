import streamlit as st
import ui.sidebar as sidebar
import state.session as session
import features.settings.page as settings_page
import features.news_analysis.page as analysis_page
import features.history.page as history_page
import features.login.page as login_page

st.set_page_config(page_title="AI news analyzer", page_icon=":sparkles:", layout="wide")

#inicializar as variaveis de sessão
session.init_session()

if not st.session_state.logged_in:
    login_page.render()
    st.stop()

#inicializar o sidebar
current_page = sidebar.render_sidebar()

#roteamento das páginas
if current_page == 'analysis':
    analysis_page.render()
elif current_page == 'history':
    history_page.render()
elif current_page == 'settings':
    settings_page.render()
