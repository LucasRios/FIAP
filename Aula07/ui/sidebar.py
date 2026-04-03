import streamlit as st

def render_sidebar():
    st.sidebar.title(f"🚀 FIAP AI News")

    if st.session_state.logged_in:
        st.sidebar.write(f"Olá, {st.session_state.username}")
        st.sidebar.markdown("---")

        role = st.session_state.role

        # Sempre disponível
        if st.sidebar.button("Analisar Notícia"):
            st.session_state.page = "analysis"

        # Apenas admin
        if role == "admin":
            if st.sidebar.button("Histórico"):
                st.session_state.page = "history"

            if st.sidebar.button("Configurações"):
                st.session_state.page = "settings"

        st.sidebar.markdown("---")

        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    return st.session_state.page       