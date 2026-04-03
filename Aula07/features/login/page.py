import streamlit as st
from pipelines.auth_pipeline import login_user

def render():
    st.title("Login")

    with st.form("login_form"):
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")

        if st.form_submit_button("Entrar"):
            result = login_user(user, pw)

            if result["success"]:
                st.session_state.logged_in = True
                st.session_state.username = result["username"]
                st.session_state.role = result["role"]
                st.rerun()
            else:
                st.error(result["error"])