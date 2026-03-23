# =============================================================================
# ARQUIVO: app.py — O Maestro da Aplicação
# =============================================================================
# Responsabilidade: Este é o "Ponto de Entrada" (Entry Point). 
# Imagine que ele é o recepcionista de um prédio: ele sabe onde cada sala 
# está e direciona o usuário, mas não faz o trabalho técnico de cada sala.
# =============================================================================

import streamlit as st  # Importa o framework principal para criar a interface web

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO GLOBAL DA PÁGINA
# -----------------------------------------------------------------------------
# O Streamlit exige que esta seja a PRIMEIRA instrução de interface.
# Ela define o que aparece na aba do navegador e como o layout se comporta.
st.set_page_config(
    page_title="AI News Analyzer",  # Título que aparece na aba do navegador
    page_icon="📰",                 # Ícone (favicon) da aba
    layout="wide"                   # Usa toda a largura da tela (melhor para dashboards)
)

# -----------------------------------------------------------------------------
# IMPORTAÇÃO DE MÓDULOS INTERNOS (A nossa estrutura de pastas)
# -----------------------------------------------------------------------------
# Aqui estamos trazendo as peças de outras pastas para dentro do app principal.
# Isso mantém o código organizado e fácil de dar manutenção.

# 1. Gerenciamento de Memória: Inicializa variáveis que o app precisa "lembrar"
from state.session import init_session          

# 2. Navegação: Traz o componente visual do menu lateral
from ui.sidebar import render_sidebar           

# 3. Páginas/Funcionalidades: Cada variável abaixo representa uma "tela" do sistema
from features.news_analysis import page as analysis_page
from features.history import page as history_page
from features.settings import page as settings_page

# -----------------------------------------------------------------------------
# PASSO 1: INICIALIZAR O ESTADO (Session State)
# -----------------------------------------------------------------------------
# O Streamlit "recarrega" o script do zero a cada clique. 
# Chamamos init_session() para garantir que variáveis globais (como logins ou 
# histórico) não sejam apagadas a cada interação do usuário.
init_session()

# -----------------------------------------------------------------------------
# PASSO 2: RENDERIZAR O MENU LATERAL (Sidebar)
# -----------------------------------------------------------------------------
# Chamamos a função que desenha os botões/links no lado esquerdo.
# Ela foi programada para nos devolver (return) o nome da página que o usuário clicou.
# Exemplo: Se o usuário clicou em "Histórico", a variável current_page será "history".
current_page = render_sidebar()

# -----------------------------------------------------------------------------
# PASSO 3: ROTEAMENTO (Decidir qual tela mostrar)
# -----------------------------------------------------------------------------
# Aqui usamos uma estrutura condicional simples (if/elif) para "desenhar" a tela certa.
# Cada página tem uma função .render() que contém todo o conteúdo visual daquela seção.

# Se a página ativa for a de análise:
if current_page == "analysis":
    analysis_page.render()

# Se o usuário escolheu ver o histórico:
elif current_page == "history":
    history_page.render()

# Se o usuário clicou em configurações:
elif current_page == "settings":
    settings_page.render()

# -----------------------------------------------------------------------------
# Para adicionar uma nova página, você precisaria de 3 passos:
# 1. Criar o arquivo na pasta /features.
# 2. Importar ele aqui no topo do app.py.
# 3. Adicionar um novo 'elif' para chamar o .render() dele.
# -----------------------------------------------------------------------------