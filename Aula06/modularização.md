# Arquitetura Moderna de **AI SaaS modernos**

## 1. O Core da Arquitetura AI SaaS
A base de um SaaS (Software as a Service) de IA moderno não é apenas o modelo (LLM), mas como ele se comunica com o resto do sistema.

- *O Princípio do Desacoplamento*: A interface (o que o usuário vê) nunca deve saber como a IA processa o dado. Ela apenas envia um pedido e espera uma resposta.
- *Stack Tecnológica Comum*: Frontend Prototipagem: Streamlit, Gradio (foco em velocidade).
 
**Python com interfaces rápidas** costuma seguir três princípios estruturais principais:

1.  **Feature-first architecture**
2.  **Pipelines de IA isolados**
3.  **Camada de interface extremamente fina**

A ideia central é separar **interface**, **lógica de produto** e
**processamento de IA**, evitando acoplamento.

Estrutura conceitual:

    UI
    ↓
    Feature
    ↓
    Pipeline
    ↓
    Providers

ou de forma mais completa:

    Interface (UI)
    ↓
    Features (casos de uso do produto)
    ↓
    Pipelines (fluxos de IA)
    ↓
    Providers (LLM, embeddings, APIs externas)

Esse modelo permite que **cada camada evolua independentemente**, algo
essencial em produtos que usam IA, onde os provedores e modelos mudam
com frequência.

------------------------------------------------------------------------

# 1. Feature-First Architecture

Arquitetura **feature-first** organiza o código em torno de
**funcionalidades do produto**, e não em torno de tecnologias.

Arquiteturas tradicionais normalmente seguem estruturas como:

    controllers/
    services/
    models/
    views/

ou

    frontend/
    backend/
    database/

Essas estruturas organizam o projeto **por tipo técnico**, não por
**capacidade do produto**.

Em produtos com IA isso gera problemas, porque:

-   funcionalidades de IA misturam várias camadas
-   pipelines de IA são complexos
-   features crescem rapidamente

Por isso muitos sistemas modernos adotam **feature-first**.

Exemplo:

    features/
        chat/
            chat_service.py
            chat_pipeline.py
            chat_ui.py

        summarization/
            summarization_service.py
            summarization_pipeline.py
            summarization_ui.py

Cada pasta contém **tudo que aquela funcionalidade precisa**.

Isso cria várias vantagens:

### Coesão

Tudo que pertence ao **chat**, por exemplo, está em um único lugar.

### Evolução independente

Se um produto adiciona uma nova feature (exemplo: geração de imagens),
basta criar:

    features/image_generation/

sem alterar o restante do sistema.

### Escalabilidade de times

Em produtos maiores, equipes trabalham por **feature**, não por
tecnologia.

Exemplo:

-   Time Chat
-   Time Search
-   Time Agents

Cada equipe mantém sua própria pasta de feature.

### Organização mental do produto

A estrutura do código reflete diretamente **o que o produto faz**.

------------------------------------------------------------------------

# 2. Pipelines de IA isolados

A segunda ideia fundamental é separar **o fluxo de IA do resto da
aplicação**.

Pipelines de IA normalmente incluem várias etapas:

1.  preparação de dados
2.  chamadas de modelo
3.  pós-processamento
4.  avaliação
5.  armazenamento de resultado

Exemplo de pipeline simples:

    Pergunta do usuário
    ↓
    Busca de contexto (RAG)
    ↓
    Construção de prompt
    ↓
    Chamada do LLM
    ↓
    Pós-processamento
    ↓
    Resposta

Esse fluxo não deve ficar dentro da UI nem da feature diretamente.

Ele fica isolado em **pipelines**.

Exemplo:

    pipelines/
        rag_pipeline.py
        summarization_pipeline.py
        agent_pipeline.py

Isso traz várias vantagens importantes.

### Reutilização

O mesmo pipeline pode ser usado por:

-   Streamlit
-   API
-   CLI
-   jobs de backend
-   agentes

Exemplo:

    Streamlit UI
    ↓
    API endpoint
    ↓
    CLI
    ↓
    todos usam rag_pipeline

### Testabilidade

Pipelines isolados podem ser testados sem UI.

Exemplo:

    pytest pipelines/rag_pipeline.py

### Evolução de modelos

Trocar um modelo não exige alteração da interface.

Exemplo:

    OpenAI → Anthropic

apenas muda o provider.

### Observabilidade

Sistemas modernos registram:

-   latência
-   tokens
-   custo
-   qualidade

Isso é feito **dentro do pipeline**.

------------------------------------------------------------------------

# 3. Interface extremamente fina

A UI em produtos modernos de IA tende a ser **muito simples**.

Ela apenas:

1.  coleta input
2.  chama uma feature
3.  exibe resultado

Exemplo Streamlit:

``` python
question = st.text_input("Pergunta")

if st.button("Enviar"):
    response = chat_feature.run(question)
    st.write(response)
```

Note que a UI **não contém lógica de IA**.

Ela não sabe:

-   qual modelo está sendo usado
-   se há RAG
-   se existe vector search
-   se existe agente

Tudo isso está escondido nas camadas abaixo.

Isso gera benefícios importantes.

### Substituição fácil da interface

O mesmo backend pode servir:

-   Streamlit
-   Gradio
-   API REST
-   frontend em React
-   aplicativo mobile

### Redução de bugs

Interface simples significa menos lógica duplicada.

### Evolução independente

A UI pode mudar sem afetar o pipeline.

------------------------------------------------------------------------

# 4. Estrutura de diretórios

Uma organização comum desse padrão é:

    app.py

    ui/
        components/
            chat_box.py
            feedback_widget.py
            history_table.py

    features/
        chat/
            chat_service.py
            chat_controller.py

        feedback/
            feedback_service.py

    pipelines/
        rag_pipeline.py
        summarization_pipeline.py

    providers/
        llm_provider.py
        embeddings_provider.py
        search_provider.py

    state/
        session_state.py

Cada camada possui responsabilidades bem definidas.

------------------------------------------------------------------------

# 5. Responsabilidade de cada camada

## ui/ - O balcão de atendimento.

Responsabilidade: Puramente visual e interativa.

- O que faz: Captura text_input, gerencia o estado de botões e exibe st.spinner ou barras de progresso.
- O que NÃO faz: Não importa o openai ou o langchain aqui. Ela chama uma função da camada de Feature.
- Exemplo: O usuário cola um link de uma notícia. A UI apenas valida se o link é uma URL válida e passa a bola adiante.

Contém **componentes visuais reutilizáveis**.

Exemplos:

-   chat interface
-   botões
-   widgets
-   tabelas
-   gráficos
-   formulários

Esses componentes **não possuem lógica de IA**.

Eles apenas exibem dados.

Exemplo:

    ui/components/chat_box.py
    ui/components/feedback_buttons.py
    ui/components/history_chart.py

Isso permite reutilizar o mesmo componente em várias páginas.

------------------------------------------------------------------------

## features/ - O gerente que entende o pedido.

Features representam **funcionalidades do produto**.

Responsabilidade: Define o que o nosso produto/interface tem.
Conceito: Uma aplicação pode ter várias features: "Resumo de PDFs", "Chat Jurídico", "Gerador de Posts". Pensando no streamLit isso é pensado como janelas.
Orquestração: O Controller da feature recebe o dado da UI, decide qual Pipeline chamar e formata a resposta final para que a UI consiga exibir.

Exemplos:

-   chat
-   resumo de documentos
-   análise de texto
-   geração de código
-   classificação

Cada feature:

-   recebe inputs
-   chama pipelines
-   retorna resultados prontos para a UI.

Exemplo:

    features/chat/chat_service.py

``` python
from pipelines.rag_pipeline import run_rag

def chat(question):
    return run_rag(question)
```

A feature funciona como **camada de orquestração do produto**.

------------------------------------------------------------------------

## pipelines/ - A cozinha que prepara o prato seguindo uma receita.

Aqui ficam os **fluxos de IA**.

Responsabilidade: Onde a "mágica" técnica acontece.
Segue uma sequência de funções e passos para processar a informação e retornar para a interface

Por exemplo
- Recebe a query.
- Transforma em vetor (Embedding).
- Busca no banco (Retrieval).
- Monta o prompt com o contexto.
- Chama a LLM.

Vantagem: Este pipeline pode ser testado isoladamente com scripts de avaliação, sem precisar rodar a interface.

Exemplos:

-   RAG
-   agentes
-   chains
-   pipelines multimodais

Um pipeline pode incluir:

    input
    ↓
    embeddings
    ↓
    vector search
    ↓
    prompt construction
    ↓
    LLM
    ↓
    output formatting

Pipelines podem crescer bastante em sistemas reais.

Exemplo:

    pipelines/
        rag_pipeline.py
        agent_pipeline.py
        classification_pipeline.py

Eles são **o coração do sistema de IA**.

------------------------------------------------------------------------

## providers/ - O fornecedor dos ingredientes (os modelos e dados).

Providers são as **integrações externas**.

Responsabilidade: Isolar as bibliotecas externas e APIs.
Abstração: Se você usa o Pinecone hoje e quer mudar para o Weaviate amanhã, você só mexe aqui.
Exemplos: Wrappers para APIs da OpenAI, funções de conexão com banco SQL, ou scripts de web scraping (BeautifulSoup/Selenium).

Exemplos:

-   LLM APIs
-   serviços de embeddings
-   bancos vetoriais
-   scraping
-   APIs externas

Arquivos típicos:

    providers/
        openai_provider.py
        anthropic_provider.py
        pinecone_provider.py
        search_provider.py

A vantagem dessa camada é permitir **troca de fornecedor sem alterar
pipelines**.

Exemplo:

antes:

    OpenAI

depois:

    Anthropic

Apenas o provider muda.

------------------------------------------------------------------------

## state/

Aplicações interativas precisam de **estado**.

No caso de Streamlit isso normalmente usa:

    st.session_state

Mas em sistemas maiores o estado pode incluir:

-   histórico de chat
-   feedback do usuário
-   preferências
-   configurações
-   cache de resultados

Exemplo:

    state/
        chat_state.py
        settings_state.py

Isso centraliza o gerenciamento de estado.
 
------------------------------------------------------------------------

# 6. Exemplos em empresas grandes

Esse tipo de separação aparece em vários projetos modernos.

## OpenAI

Isso aparece no framework OpenAI Agents SDK.

Nesse modelo existem camadas como:

UI → UI
Agents → Features
Runtime → Pipelines
Models / Tools → Providers
Memory → State

------------------------------------------------------------------------

## LangChain

O framework LangChain popularizou a ideia de
**pipelines modulares de LLM**.

Interface externa → UI
Agents / Chains → Features
Chains → Pipelines
Models → Providers
Memory → State

Essa separação inspirou muitas arquiteturas de AI SaaS.

------------------------------------------------------------------------

## LlamaIndex

Outro exemplo é o framework LlamaIndex.

Interface -> UI
Query Engine -> Features
Retrieval + synthesis pipeline -> Pipelines
LLM + embeddings -> Providers
Session / memory -> State

Isso corresponde diretamente ao conceito de **pipeline de IA isolado**.

------------------------------------------------------------------------

## Microsoft AI apps

A Microsoft recomenda arquiteturas semelhantes em aplicações com IA.

A estrutura costuma separar:

Frontend - UI
Orchestration - Features
Skills - Pipelines
Models / Connectors - Providers
Application memory - State

------------------------------------------------------------------------

# 8. Benefícios dessa arquitetura

Principais vantagens:

### Baixo acoplamento

Mudanças em uma camada não quebram outras.

### Troca fácil de modelos

LLM providers mudam rapidamente.

Arquitetura desacoplada permite trocar modelos sem reescrever o sistema.

### Escalabilidade

Times podem trabalhar em features diferentes.

### Reutilização

Pipelines podem ser usados por:

-   UI
-   API
-   jobs
-   agentes

### Testabilidade

Pipelines e providers podem ser testados isoladamente.

------------------------------------------------------------------------

# 9. Relação com o app construído em aula

### app.py
``` python

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


```

### ui/sidebar.py
``` python
# =============================================================================
# ui/sidebar.py — Componente de navegação lateral
#
# Responsabilidade: SOMENTE renderizar o menu e retornar qual página foi
# selecionada. Não contém lógica de negócio.
# A ideia é manter o roteamento centralizado e fácil de modificar.
# =============================================================================

import streamlit as st 

def render_sidebar():
    st.sidebar.title("🚀 FIAP AI News")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Navegação")
    
    # Criando botões que funcionam como links de navegação
    if st.sidebar.button("Analisar Notícia", use_container_width=True):
        st.session_state.page = "analysis"
    
    if st.sidebar.button("Histórico", use_container_width=True):
        st.session_state.page = "history"
        
    if st.sidebar.button("Configurações", use_container_width=True):
        st.session_state.page = "settings"
         
    
    return st.session_state.page

```

### state/session.py
``` python
# =============================================================================
# state/session.py — Gerenciamento do estado global da sessão
#
# Responsabilidade: centralizar a inicialização de TODAS as variáveis de
# st.session_state. Isso evita KeyError em qualquer outro módulo que leia
# essas chaves antes de elas existirem.
#
# Regra: cada variável de estado TEM que ser declarada aqui com seu valor
# padrão. Se precisar de um novo campo, adicione aqui primeiro.
# =============================================================================

import streamlit as st

def init_session():
    """
    Inicializa as variáveis de sessão com valores padrão.

    O Streamlit mantém st.session_state entre re-renders da mesma sessão,
    mas reseta tudo ao recarregar a página. Esta função usa o padrão
    """

    # ------------------------------------------------------------------
    # Estado da análise atual
    # ------------------------------------------------------------------
 
    if "page" not in st.session_state:
        st.session_state.page = "analysis"
    
    # ------------------------------------------------------------------
    # Histórico de análises realizadas na sessão
    # Cada item é um dicionário com: url, summary, sentiment, feedback
    # ------------------------------------------------------------------
    if "history" not in st.session_state:
        st.session_state.history = []

    # Resumo gerado pelo modelo LLM
    if "summary" not in st.session_state:
        st.session_state.summary = None

    # Resultado da análise de sentimento: dicionário com label e score
    # Ex: {"label": "Positivo", "score": 0.87, "emoji": "😊"}  
    if "sentiment" not in st.session_state:
        st.session_state.sentiment = None

    # Texto bruto extraído pelo scraper
    if "article_text" not in st.session_state:
        st.session_state.article_text = ""

    # Modelo escolhido na página de configurações 
    if "model" not in st.session_state:
        st.session_state.model = "medium"

    # Modelo escolhido na página de configurações 
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7

    # URL digitada pelo usuário (espelho do widget url_input)
    if "current_url" not in st.session_state:
        st.session_state.current_url = ""

    if "df_final" not in st.session_state:
        st.session_state.df_final = None
        
    if "analise" not in st.session_state:
        st.session_state.analise = None        



```

### providers/scraper_nlp_provider.py
``` python
# =============================================================================
# providers/scraper_nlp_provider.py
#
# PROVIDER DE COLETA E ANÁLISE NLP — Scraping, limpeza e análise de sentimento
# via léxico local (sem dependência de API externa).
#
# -----------------------------------------------------------------------------
# INSTALAÇÃO — rode esses comandos no terminal antes de executar:
#
#   pip install requests beautifulsoup4 textblob nltk scikit-learn matplotlib pandas
#
# -----------------------------------------------------------------------------
#
# Como executar:
#   python scraper_nlp_provider.py
#
# Como importar no pipeline:
#   from providers.scraper_nlp_provider import get_df_final, get_analise
# =============================================================================

import requests
import pandas as pd
import re
import os
import matplotlib
import matplotlib.pyplot as plt
import nltk

from bs4 import BeautifulSoup
from textblob import TextBlob
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

# from IPython.display import display, Markdown
# IPython.display é exclusivo do ambiente Jupyter/Colab.
# No VS Code usamos print() para texto e retornamos figuras do matplotlib
# para que o Streamlit possa renderizá-las com st.pyplot().

# Matplotlib em modo não-interativo: evita que plt.show() abra janela
# separada ao rodar via Streamlit (o Streamlit renderiza a figura via st.pyplot).
# No terminal standalone, show() continua funcionando normalmente.
matplotlib.use('Agg')  # sem isso, plt.show() trava em alguns ambientes sem display

# Download de recursos essenciais do NLTK (execução local)
# quiet=True suprime a saída verbosa — os arquivos ficam em ~/nltk_data
nltk.download('punkt',     quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

print("✅ Ambiente configurado com sucesso (Modo Offline).")


# =============================================================================
# Variáveis de módulo — preenchidas após run_pipeline()
# Ficam expostas para importação pelo news_pipeline.py
# =============================================================================
df_final_global = None   # DataFrame limpo e estruturado
analise_global  = None   # Dicionário com resultado da análise NLP


# =============================================================================
# ETAPA 1 — Coleta via Scraping (RPA com requests + BeautifulSoup)
# =============================================================================

def coleta(urls: list) -> pd.DataFrame:
    """
    Faz scraping das URLs informadas e extrai o conteúdo textual relevante.

    Args:
        urls (list): Lista de URLs a coletar.

    Returns:
        pd.DataFrame: Colunas ["url", "texto_bruto"] com o conteúdo coletado.
    """
    dataset_bruto = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for url in urls:
        try:
            print(f"🔍 [RPA] Coletando: {url}")
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')

            # Extrai parágrafos e títulos significativos
            fragments = [tag.text.strip() for tag in soup.find_all(['p', 'h1', 'h2'])]
            content   = " ".join([f for f in fragments if len(f) > 30])

            if len(content) > 100:
                dataset_bruto.append({"url": url, "texto_bruto": content})

        except Exception as e:
            print(f"❌ [Erro] Falha em {url}: {e}")

    return pd.DataFrame(dataset_bruto)


# =============================================================================
# ETAPA 2 — Preparação e Limpeza do Texto
# =============================================================================

def preparacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza o texto bruto, remove duplicatas e exporta CSV estruturado.

    Args:
        df (pd.DataFrame): DataFrame com coluna "texto_bruto".

    Returns:
        pd.DataFrame: DataFrame com coluna "texto_limpo" adicionada.
    """
    if df.empty:
        return df

    print("🧹 [Processamento] Normalizando dados...")

    def limpar_texto(texto):
        texto = texto.lower()
        texto = re.sub(r'[^a-zá-ú0-9\s\.]', '', texto)  # Mantém letras, números e pontos
        return re.sub(r'\s+', ' ', texto).strip()

    df['texto_limpo'] = df['texto_bruto'].apply(limpar_texto)
    df = df.drop_duplicates(subset=['texto_limpo'])
    df = df[df['texto_limpo'].str.len() > 150]

    df.to_csv("dataset_estruturado.csv", index=False)
    return df


# =============================================================================
# ETAPA 3 — Análise NLP Local (Sentimento + TF-IDF + Sumarização)
# =============================================================================

def analise_local(df: pd.DataFrame) -> dict:
    """
    Executa análise NLP completa sobre o DataFrame limpo:
      1. Sentimento via TextBlob (polaridade léxica)
      2. Extração de temas via TF-IDF
      3. Sumarização extrativa simples

    Args:
        df (pd.DataFrame): DataFrame com coluna "texto_limpo".

    Returns:
        dict: Resultado completo da análise com as chaves:
              overall_sentiment, polarity_val, themes, summary, distribution
    """
    print("⚙️ [NLP Local] Iniciando processamento estatístico...")

    texto_completo = " ".join(df['texto_limpo'].tolist())

    # 1. Análise de Sentimento (Polaridade)
    # Nota: TextBlob em PT-BR funciona melhor com tradução ou léxicos simples.
    # Aqui usamos polaridade média dos documentos.
    sentiment_scores = [TextBlob(txt).sentiment.polarity for txt in df['texto_limpo']]
    avg_polarity     = sum(sentiment_scores) / len(sentiment_scores)

    overall = (
        "Positivo" if avg_polarity >  0.05 else
        "Negativo" if avg_polarity < -0.05 else
        "Neutro"
    )

    # 2. Extração de Temas (TF-IDF)
    vectorizer  = TfidfVectorizer(max_features=10, stop_words=stopwords.words('portuguese'))
    tfidf_matrix = vectorizer.fit_transform(df['texto_limpo'])
    temas       = vectorizer.get_feature_names_out()

    # 3. Sumarização Extrativa Simples
    sentencas = sent_tokenize(texto_completo)
    resumo    = " ".join(sentencas[:3]) + "..."  # Pega as premissas iniciais dos textos

    return {
        "overall_sentiment": overall,
        "polarity_val":      avg_polarity,
        "themes":            list(temas),
        "summary":           resumo,
        "distribution": {
            "positive": len([s for s in sentiment_scores if s >  0.05]) / len(sentiment_scores) * 100,
            "neutral":  len([s for s in sentiment_scores if -0.05 <= s <= 0.05]) / len(sentiment_scores) * 100,
            "negative": len([s for s in sentiment_scores if s < -0.05]) / len(sentiment_scores) * 100,
        }
    }

 

# =============================================================================
# PIPELINE PRINCIPAL — run_pipeline()
# =============================================================================

# URLs padrão — podem ser sobrescritas ao chamar run_pipeline(urls=[...])
URLS_PADRAO = [
    "https://www.cnnbrasil.com.br/tecnologia/",
    "https://g1.globo.com/tecnologia/"
]

def run_pipeline(urls: list = None) -> tuple:
    """
    Executa o pipeline completo de coleta e análise NLP.

    Args:
        urls (list): Lista de URLs para coletar. Se None, usa URLS_PADRAO.

    Returns:
        tuple: (df_final, resultado_analise)
               df_final        → pd.DataFrame com texto limpo estruturado
               resultado_analise → dict com sentimento, temas e sumarização
    """
    global df_final_global, analise_global

    urls = urls or URLS_PADRAO

    # ── Etapa 1: Coleta ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📡 ETAPA 1 — Coleta via Scraping")
    print("=" * 60)
    df_bruto = coleta(urls)

    # ── Etapa 2: Preparação ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🧹 ETAPA 2 — Limpeza e Preparação")
    print("=" * 60)
    df_final_global = preparacao(df_bruto)

    # ── Etapa 3: Análise NLP ──────────────────────────────────────────────────
    if not df_final_global.empty:
        print("\n" + "=" * 60)
        print("🤖 ETAPA 3 — Análise NLP Local")
        print("=" * 60)
        analise_global = analise_local(df_final_global)
    else:
        print("❌ Nenhum dado coletado para análise.")
        analise_global = {}

    return df_final_global, analise_global


# =============================================================================
# Funções auxiliares — interface para o news_pipeline.py
# =============================================================================

def get_df_final(urls: list = None) -> pd.DataFrame:
    """
    Retorna df_final_global, executando run_pipeline() se ainda não foi rodado.
    Usada pelo news_pipeline.py para acessar o dataset estruturado.
    """
    global df_final_global
    if df_final_global is None or df_final_global.empty:
        print("📡 Dataset não encontrado em memória — iniciando pipeline...")
        run_pipeline(urls=urls)
    return df_final_global


def get_analise(urls: list = None) -> dict:
    """
    Retorna o dicionário de análise NLP, executando run_pipeline() se necessário.
    Usada pelo news_pipeline.py para obter sentimento, temas e sumarização.
    """
    global analise_global
    if analise_global is None:
        run_pipeline(urls=urls)
    return analise_global


# =============================================================================
# Ponto de entrada
# ALTERADO: o código de execução ficava solto no nível do módulo, o que
# causava execução automática ao fazer `import` em outros arquivos.
# Protegido com __main__: só executa quando chamado diretamente pelo terminal.
# =============================================================================
if __name__ == "__main__":
    print("🚀 Executando pipeline completo...")
    df, resultado = run_pipeline()
    print(f"\n🏁 Pipeline finalizado. {len(df)} documentos processados.")

```

### pipelines/news_pipeline.py
``` python
# =============================================================================
# ARQUIVO: pipelines/news_pipeline.py
# =============================================================================
# Responsabilidade: Orquestrar o fluxo de processamento de dados (ETL).
# ETL significa: Extract (Extrair), Transform (Transformar) e Load (Carregar).
# Este arquivo conecta as funções de baixo nível do provedor de NLP com 
# a interface visual do Streamlit.
# =============================================================================

# Importamos as funções especializadas do nosso "Provedor" de inteligência artificial.
# etapa_1: Busca a notícia na web.
# etapa_2: Limpa o texto (remove HTML, anúncios, etc).
# etapa_analise_local: Aplica os modelos de IA para resumo e sentimento.
from providers.scraper_nlp_provider import (
    coleta, 
    preparacao, 
    analise_local
)

def analyze_news(url: str):
    """
    Função principal que orquestra o fluxo de dados. 
    Recebe uma URL (string) e retorna um dicionário estruturado ou None.
    """
    
    # -------------------------------------------------------------------------
    # 1. COLETA (EXTRAÇÃO)
    # -------------------------------------------------------------------------
    # Enviamos a URL dentro de uma lista [url] para a função de coleta.
    # df_bruto é um DataFrame do Pandas contendo o que foi baixado do site.
    df_bruto = coleta([url])
    
    # Validação de segurança: Se a coleta falhou (URL inválida ou site bloqueado),
    # interrompemos o processo aqui para evitar erros no código seguinte.
    if df_bruto.empty:
        return None

    # -------------------------------------------------------------------------
    # 2. LIMPEZA E PREPARAÇÃO (TRANSFORMAÇÃO)
    # -------------------------------------------------------------------------
    # O texto bruto de um site vem com "sujeira". Esta etapa isola apenas 
    # o corpo do texto da notícia, tratando pontuação e caracteres especiais.
    df_final = preparacao(df_bruto)

    # -------------------------------------------------------------------------
    # 3. ANÁLISE (IA E PROCESSAMENTO)
    # -------------------------------------------------------------------------
    if not df_final.empty:
        # Aqui a mágica acontece: o modelo de NLP lê o texto limpo e gera:
        # - Um resumo automático.
        # - A polaridade (positivo/negativo).
        # - A distribuição de confiança dos sentimentos.
        resultado_analise = analise_local(df_final)
        
        # ---------------------------------------------------------------------
        # 4. FORMATAÇÃO DO CONTRATO (RETORNO)
        # ---------------------------------------------------------------------
        # Não retornamos o DataFrame bruto para a UI.
        # Criamos um "Dicionário de Resposta" limpo. Isso separa a lógica de dados
        # da lógica de visualização. Se mudarmos a IA no futuro, a UI nem percebe.
        return {
            "article": df_final.iloc[0]['texto_bruto'],  # Texto original completo
            "summary": resultado_analise['summary'],      # Resumo gerado pela IA
            "sentiment": {
                "label": resultado_analise['overall_sentiment'], # Ex: "Positivo"
                "score": resultado_analise['polarity_val'],      # Valor numérico da análise
                "distribution": resultado_analise['distribution'], # Dados para gerar gráficos
                # Lógica visual simples: escolhe o emoji baseado no texto do sentimento
                "emoji": "😊" if resultado_analise['overall_sentiment'] == "Positivo" else "😐"
            }
        }
    
    # Se algo falhou no meio do caminho, retornamos Nada (None)
    return None
```

### features/history/page.py
``` python
# =============================================================================
# features/history/page.py — View da página de histórico
#
# Responsabilidade: exibir todas as análises realizadas na sessão atual,
# com tabela, gráfico de feedback e visualização de itens individuais.
# =============================================================================

import streamlit as st
import pandas as pd

from ui.charts import render_sentiment_chart


def render():
    """
    Renderiza a página de histórico de análises.

    Estrutura visual:
      [Tabela completa do histórico]
           ↓
      [Gráfico de distribuição de feedback] (se houver feedback)
           ↓
      [Visualização de análise individual selecionada]
    """

    st.title("Histórico de Análises")
    st.markdown("Consulte todas as notícias analisadas nesta sessão.")
    st.markdown("---")

    history = st.session_state.history

    # ------------------------------------------------------------------
    # Caso não haja histórico: exibe mensagem informativa
    # ------------------------------------------------------------------
    if len(history) == 0:
        st.info("Nenhuma análise registrada ainda. Vá para **Analisar notícia** para começar.")
        return

    # ------------------------------------------------------------------
    # Converte a lista de dicionários em DataFrame para exibição
    # ------------------------------------------------------------------
    df = pd.DataFrame(history)

    # Renomeia colunas para exibição mais amigável
    column_labels = {
        "url":        "URL",
        "summary":    "Resumo",
        "sentimento": "Sentimento",
        "feedback":   "Feedback",
    }
    df_display = df.rename(columns=column_labels)

    st.subheader(f"📊 {len(history)} análise(s) registrada(s)")
    st.dataframe(df_display, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Gráfico de distribuição de feedback (só aparece se houver feedback)
    # ------------------------------------------------------------------
    if "feedback" in df.columns:

        st.subheader("👍👎 Distribuição de Feedback")

        feedback_counts = (
            df["feedback"]
            .value_counts()
            .rename_axis("Tipo")
            .reset_index(name="Quantidade")
            .set_index("Tipo")
        )

        st.bar_chart(feedback_counts)

    # ------------------------------------------------------------------
    # Gráfico de distribuição de sentimentos
    # ------------------------------------------------------------------
    if "sentimento" in df.columns:

        st.subheader("🧠 Distribuição de Sentimentos")

        sentiment_counts = (
            df["sentimento"]
            .value_counts()
            .rename_axis("Sentimento")
            .reset_index(name="Quantidade")
            .set_index("Sentimento")
        )

        st.bar_chart(sentiment_counts)

        st.markdown("---")

        # 2. IMPLEMENTAÇÃO DO GRÁFICO
        st.markdown("---")
        st.subheader("Gráfico de Distribuição")
            
        # Chamamos a função da UI passando os dados do session_state
        # Contamos as ocorrências no DataFrame
        counts = df["sentimento"].value_counts().to_dict()
    
        # Mapeamos para o formato que a função da UI espera
        # (Ajuste as chaves para baterem com o que o provider usa: 'positive', etc)
        dist_global = {
            "positive": counts.get("Positivo", 0),
            "neutral": counts.get("Neutro", 0),
            "negative": counts.get("Negativo", 0)
        }

        if any(dist_global.values()):
            render_sentiment_chart(dist_global)
 
    # ------------------------------------------------------------------
    # Seletor para visualizar uma análise específica do histórico
    # ------------------------------------------------------------------
    st.subheader("🔎 Visualizar análise individual")

    # Cria rótulos amigáveis: "Análise 1 — https://..."
    options = {
        f"Análise {i + 1} — {row['url'][:60]}...": i
        for i, row in df.iterrows()
    }

    selected_label = st.selectbox("Selecionar análise", list(options.keys()))
    selected_idx   = options[selected_label]

    row = df.loc[selected_idx]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Sentimento", row.get("sentimento", "N/A"))

    with col2:
        st.metric("Feedback",   row.get("feedback",   "N/A"))

    st.subheader("Resumo")
    st.write(row["summary"])
```

### features/news_analysis/page.py
``` python

# =============================================================================
# features/news_analysis/page.py — View da página de análise de notícias
#
# Responsabilidade: renderizar a interface de análise. Esta camada SÓ lida
# com exibição
# =============================================================================

import streamlit as st 
from pipelines.news_pipeline import analyze_news 


def render():
    """
    Renderiza a página principal de análise de notícias.

    Estrutura visual:
      [Input de URL] + [Botão Analisar]
           ↓
      [Tabs: Sentimento | Resumo | Texto extraído]
           ↓
      [Seção de Feedback]
    """

    st.title("🔍 Análise de Notícias com IA")
    st.markdown("Insira a URL de uma notícia e a IA irá extrair, processar e analisar o conteúdo.")
    st.markdown("---")

    # ------------------------------------------------------------------
    # Seção de input
    # ------------------------------------------------------------------
    st.subheader("1. Informe a URL")

    url = st.text_input(
        "URL da notícia",
        placeholder="https://g1.globo.com/...",
        key="url_input"    # chave no session_state
    )

    # on_click= passa a função sem chamá-la; o Streamlit chama ao clicar
    st.button(
        "🚀 Executar análise",
        on_click=run_analysis,
        type="primary"
    )

    # ------------------------------------------------------------------
    # Se ainda não há resultado, exibe instrução e encerra a renderização
    # ------------------------------------------------------------------
    if not st.session_state.summary:
        st.info("⬆️ Insira uma URL acima e clique em **Executar análise** para começar.")
        return

    st.markdown("---")
    st.subheader("2. Resultados")

    # ------------------------------------------------------------------
    # Tabs de resultado: Sentimento | Resumo | Texto bruto
    # ------------------------------------------------------------------
    tab_sentiment, tab_summary, tab_raw = st.tabs([
        "🧠 Sentimento",
        "📝 Resumo",
        "📄 Texto extraído",
    ])

    # ---- Tab 1: Análise de Sentimento --------------------------------
    with tab_sentiment:

        sentiment = st.session_state.sentiment

        if sentiment:
            st.subheader("Sentimento detectado na notícia")

            # Exibe o sentimento em destaque com métricas do Streamlit
            col_emoji, col_label, col_score = st.columns([1, 2, 2])

            with col_emoji:
                # Emoji grande como destaque visual
                st.markdown(
                    f"<h1 style='text-align:center'>{sentiment['emoji']}</h1>",
                    unsafe_allow_html=True
                )

            with col_label:
                st.metric(
                    label="Classificação",
                    value=sentiment["label"]
                )

            with col_score:
                st.metric(
                    label="Confiança do modelo",
                    value=f"{abs(sentiment['score']) * 100:.0f}%"
                )

            # Barra de progresso visual para o score de confiança
            st.progress(abs(sentiment["score"]))

            st.caption(
                "ℹ️ A análise de sentimento indica o tom predominante da notícia "
                "com base no conteúdo textual extraído."
            )
 
        else:
            st.info("Sentimento não disponível para esta análise.")

    # ---- Tab 2: Resumo com efeito de streaming ----------------------
    with tab_summary:

        st.subheader("Resumo gerado pelo modelo")

        # Simula efeito de streaming: exibe palavra por palavra
        # Em produção com API real, usaríamos stream=True e iteraríamos
        # sobre os chunks retornados pelo modelo
        placeholder = st.empty()
        displayed_text = ""

        for word in st.session_state.summary.split():
            displayed_text += word + " "
            placeholder.write(displayed_text)

        st.markdown("---")

        # ---- Seção de feedback ------------------------------------
        st.subheader("📊 Esse resumo foi útil?")

        col_pos, col_neg = st.columns(2)

        with col_pos:
            if st.button("👍 Útil"):
                _save_feedback("positivo")
                st.success("Obrigado pelo feedback positivo!")

        with col_neg:
            if st.button("👎 Ruim"):
                _save_feedback("negativo")
                st.error("Obrigado por nos avisar! Vamos melhorar.")

    # ---- Tab 3: Texto bruto extraído --------------------------------
    with tab_raw:

        st.subheader("Texto extraído da notícia")
        st.caption("Conteúdo bruto capturado pelo scraper antes do processamento.")

        st.text_area(
            "Conteúdo",
            value=st.session_state.article_text,
            height=350,
            disabled=True     # somente leitura
        )


# =============================================================================
# Função auxiliar (privada, prefixo _) — salva feedback no histórico
# =============================================================================

def _save_feedback(feedback_type: str):
    """
    Salva a análise atual + feedback no histórico da sessão.

    Args:
        feedback_type (str): "positivo" ou "negativo"
    """
    st.session_state.history.append({
        "url":       st.session_state.current_url,
        "summary":   st.session_state.summary,
        "sentimento": st.session_state.sentiment["label"] if st.session_state.sentiment else "N/A",
        "feedback":  feedback_type,
    })

 
def run_analysis():
    """
    Callback chamado quando o usuário clica em "Executar análise".

    O Streamlit passa funções de callback para on_click= dos botões.
    Nesse momento, st.session_state.url_input já tem o valor digitado.

    Fluxo:
      1. Lê a URL do session_state (espelho do widget)
      2. Valida se a URL foi preenchida
      3. Chama a pipeline de análise
      4. Salva os resultados no session_state para a View exibir
    """

    url = st.session_state.get("url_input", "").strip()
    if not url:
        st.warning("Insira uma URL.")
        return

    # Chama o pipeline (que agora está em /pipelines)
    result = analyze_news(url=url)

    if result:
        st.session_state.article_text = result["article"]
        st.session_state.summary      = result["summary"]
        st.session_state.sentiment    = result["sentiment"]
        st.session_state.current_url  = url
    else:
        st.error("Não foi possível analisar esta URL.")


```

 

### features/settings/page.py
``` python
# =============================================================================
# features/settings/page.py — View da página de configurações
#
# Responsabilidade: permitir ao usuário ajustar os parâmetros do modelo.
# Os widgets usam key= para escrever diretamente no st.session_state,
# eliminando a necessidade de um controller separado para esta página.
# =============================================================================

import streamlit as st


def render():
    """
    Renderiza a página de configurações do modelo.

    Qualquer alteração aqui é imediatamente refletida em
    st.session_state.model e st.session_state.temperature,
    que são lidos pelo controller de análise.
    """

    st.title("⚙️ Configurações")
    st.markdown("Ajuste os parâmetros do modelo de linguagem.")
    st.markdown("---")

    # ------------------------------------------------------------------
    # Seleção do modelo
    # ------------------------------------------------------------------
    st.subheader("🤖 Modelo")

    st.selectbox(
        "Escolher modelo",
        options=["small", "medium", "large"],
        key="model",         # lê/escreve em st.session_state.model
        help=(
            "small: mais rápido, menos preciso\n"
            "medium: equilíbrio entre velocidade e qualidade\n"
            "large: mais lento, maior qualidade"
        )
    )

    # ------------------------------------------------------------------
    # Parâmetros de geração
    # ------------------------------------------------------------------
    st.subheader("🎛️ Parâmetros de geração")

    st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        key="temperature",   # lê/escreve em st.session_state.temperature
        help=(
            "Controla a 'criatividade' do modelo.\n"
            "0.0 = respostas determinísticas\n"
            "1.0 = respostas mais variadas e criativas"
        )
    )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Utilitários de cache
    # ------------------------------------------------------------------
    st.subheader("🗑️ Cache")
    st.caption(
        "O Streamlit armazena em cache resultados de scraping e LLM "
        "para evitar requisições repetidas. Limpe se precisar forçar "
        "uma nova análise de uma URL já processada."
    )

    if st.button("Limpar cache", type="secondary"):
        st.cache_data.clear()
        st.success("✅ Cache limpo com sucesso!")

```

## Referências
- Architecting AI Software Systems - Richard D. Avila, Imran Ahmad
- Orchestrating Agents and Data for Enterprise: A Blueprint Architecture for Compound AI - Eser Kandogan, Nikita Bhutani
- Pattern-Oriented Software Architecture - Frank Buschmann

OpenAI — Building agents
https://platform.openai.com/docs/guides/agents

LangChain Architecture
https://python.langchain.com/docs/concepts

LlamaIndex Architecture Overview
https://docs.llamaindex.ai/en/stable/understanding/architecture/

Microsoft — Generative AI application patterns
https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/genai-app-patterns

Feature-based architecture
https://martinfowler.com/articles/modular-monolith.html

Feature-driven architecture
https://www.thoughtworks.com/insights/blog/microservices/feature-driven-development

Stanford — Building LLM applications
https://crfm.stanford.edu/

