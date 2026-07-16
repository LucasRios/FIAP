# =============================================================================
# streamlit_pwa/app.py — Aula 23: transformando o Streamlit em PWA
#
# Responsabilidade: app introdutório mostrando como injetar o manifest e o
# service worker (os dois arquivos que fazem um site virar PWA) dentro de
# um app Streamlit comum.
#
# NOVO NESTA AULA: o uso de streamlit.components.v1.html para injetar HTML
# customizado (link do manifest + script do service worker) na página.
#
# IMPORTANTE: para o manifest.json e o sw.js serem realmente acessíveis
# via URL, você precisa de um proxy Nginx na frente do Streamlit em
# produção — veja o nginx.conf desta mesma aula.
#
# Como instalar:
#   pip install streamlit
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Análise de IA", page_icon="📰", layout="wide")


# -----------------------------------------------------------------------------
# INJETANDO O MANIFEST E O SERVICE WORKER — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# components.html insere um bloco de HTML "cru" na página. Usamos isso para
# colocar duas coisas no <head> da página que o Streamlit não expõe por
# padrão:
#   1. <link rel="manifest" ...> — diz ao navegador onde está o manifest.json
#   2. um <script> que registra o service worker (sw.js)
#
# height=0 evita que esse componente ocupe espaço visível na tela — ele
# só existe para injetar essas duas tags, não para mostrar nada ao usuário.
components.html(
    """
    <link rel="manifest" href="/manifest.json">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
          navigator.serviceWorker.register('/sw.js').then(function(registration) {
            console.log('Service Worker registrado:', registration.scope);
          });
        });
      }
    </script>
    """,
    height=0,
)

st.title("Análise de Notícias com IA")
st.caption(
    "Este app agora pode ser instalado na tela inicial do celular. "
    "No Chrome Android, o botão 'Adicionar à tela inicial' aparece "
    "automaticamente; no Safari iOS, use o menu Compartilhar."
)

texto = st.text_area("Cole o texto para análise:")
if st.button("Analisar") and texto:
    st.info("Exemplo introdutório — aqui entraria a chamada à API (Aula 13).")
