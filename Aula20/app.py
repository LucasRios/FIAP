# =============================================================================
# app.py — Aula 20: preparando o app para deploy gratuito
#
# Responsabilidade: app introdutório de um único arquivo mostrando a forma
# CORRETA de ler segredos (chaves de API) quando o app está publicado no
# Streamlit Community Cloud ou no Hugging Face Spaces — nenhuma das duas
# plataformas permite colocar segredos direto no código.
#
# NOVO NESTA AULA: os.environ.get(...) para o Hugging Face Spaces e
# st.secrets para o Streamlit Cloud, com um pequeno truque para o mesmo
# código funcionar nas duas plataformas.
#
# Como instalar:
#   pip install streamlit
# =============================================================================

import os
import streamlit as st

st.set_page_config(page_title="Deploy Gratuito", page_icon="🚀")
st.title("Verificação de segredos antes do deploy")


# -----------------------------------------------------------------------------
# ERRADO — NUNCA FAÇA ISSO (deixamos aqui só como exemplo do que NÃO fazer)
# -----------------------------------------------------------------------------
# ANTHROPIC_API_KEY = "sk-ant-abc123"   # <- vaza no GitHub, no histórico do
#                                          Git e em qualquer print de tela.


# -----------------------------------------------------------------------------
# CORRETO — lendo a chave de uma variável de ambiente — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# No Hugging Face Spaces, os segredos configurados em
# "Settings -> Repository secrets" ficam disponíveis via os.environ.
#
# No Streamlit Community Cloud, os segredos configurados em
# "Settings -> Secrets" ficam disponíveis via st.secrets (funciona como um
# dicionário). Para o MESMO código funcionar nas duas plataformas, tentamos
# primeiro st.secrets e, se não existir, caímos para os.environ.
def carregar_segredo(nome: str) -> str | None:
    """
    Tenta ler um segredo de st.secrets (Streamlit Cloud) e, se não
    encontrar, tenta os.environ (Hugging Face Spaces ou variável local).
    """
    try:
        return st.secrets[nome]
    except (KeyError, FileNotFoundError):
        return os.environ.get(nome)


ANTHROPIC_API_KEY = carregar_segredo("ANTHROPIC_API_KEY")

# Falha rápido e com uma mensagem clara — melhor avisar agora do que deixar
# o app quebrar de forma confusa na primeira chamada ao modelo.
if not ANTHROPIC_API_KEY:
    st.error(
        "ANTHROPIC_API_KEY não configurada. "
        "No Streamlit Cloud: Settings → Secrets. "
        "No Hugging Face Spaces: Settings → Repository secrets."
    )
else:
    st.success("Chave carregada com sucesso — o app está pronto para o deploy.")

st.caption(
    "Este app não expõe o valor da chave em nenhum momento — apenas "
    "confirma que ela foi encontrada."
)
