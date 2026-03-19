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
# app.py — Ponto de entrada da aplicação
#
# Responsabilidade: orquestrar o roteamento entre páginas.
# Este arquivo NÃO contém lógica de negócio nem de UI detalhada.
# Ele apenas inicializa o estado e delega a renderização para cada feature.
# =============================================================================

import streamlit as st

# Configuração global da página (deve ser a 1ª chamada Streamlit)
st.set_page_config(
    page_title="AI News Analyzer",
    page_icon="📰",
    layout="wide"
)

# Módulos internos da aplicação
from state.session import init_session          # Inicializa variáveis de sessão
from ui.sidebar import render_sidebar           # Renderiza o menu lateral
from features.news_analysis import page as analysis_page
from features.history import page as history_page
from features.settings import page as settings_page

# -----------------------------------------------------------------------------
# 1. Inicializar estado da sessão (só executa se ainda não existir)
# -----------------------------------------------------------------------------
init_session()

# -----------------------------------------------------------------------------
# 2. Renderizar sidebar e capturar a página ativa
#    A sidebar retorna um identificador string, ex: "analysis"
# -----------------------------------------------------------------------------
current_page = render_sidebar()

# -----------------------------------------------------------------------------
# 3. Roteamento: chama render() da feature correspondente
# -----------------------------------------------------------------------------
if current_page == "analysis":
    analysis_page.render()

elif current_page == "history":
    history_page.render()

elif current_page == "settings":
    settings_page.render()


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
    if st.sidebar.button("🔍 Analisar Notícia", use_container_width=True):
        st.session_state.page = "analysis"
    
    if st.sidebar.button("📜 Histórico", use_container_width=True):
        st.session_state.page = "history"
        
    if st.sidebar.button("⚙️ Configurações", use_container_width=True):
        st.session_state.page = "settings"
        
    st.sidebar.markdown("---")
    st.sidebar.caption("Desenvolvido para a aula de Arquitetura de IA")
    
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
    `setdefault` para não sobrescrever valores já definidos pelo usuário.
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


```

### providers/llm_provider.py
``` python
# =============================================================================
# providers/llm_provider.py — Integração com o modelo de linguagem (LLM)
#
# Responsabilidade: receber contexto processado e retornar resumo e análise
# de sentimento. Este provider ISOLA a dependência do modelo — se trocar de
# OpenAI para Gemini, só este arquivo muda.
#
# SIMULAÇÃO: Neste projeto as funções simulam as respostas do modelo com
# texto fixo + delay, para focar no aprendizado da arquitetura Streamlit.
# Para integrar um LLM real, substitua o corpo das funções pela chamada
# à API correspondente (openai.chat.completions.create, etc.)
# =============================================================================
 
import time
import random

 
def summarize_text(context: str, model: str) -> str:
    """
    Gera um resumo do contexto usando o modelo especificado.

    Em produção, aqui entraria a chamada real ao LLM:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"Resuma: {context}"}]
        )
        return response.choices[0].message.content

    Args:
        context (str): Texto reduzido pelo RAG provider
        model   (str): Identificador do modelo escolhido nas configurações

    Returns:
        str: Resumo gerado pelo modelo
    """

    # Simula o tempo de processamento do modelo
    time.sleep(1)

    # Resumo simulado — em produção viria da API do LLM
    return (
        f"[Modelo: {model.upper()}] Esta notícia aborda um tema de grande relevância "
        "para o cenário atual. Os principais pontos destacados incluem impactos "
        "econômicos, desdobramentos políticos e repercussão nas redes sociais. "
        "Especialistas ouvidos pela reportagem divergem sobre as consequências "
        "de longo prazo, mas concordam que o assunto demanda atenção imediata "
        "da sociedade e das autoridades competentes."
    )

 
def analyze_sentiment(context: str) -> dict:
    """
    Analisa o sentimento predominante no texto da notícia.

    Retorna um dicionário padronizado com:
      - label (str):  rótulo do sentimento em português
      - score (float): confiança do modelo (0.0 a 1.0)
      - emoji (str):  emoji representativo para exibição na UI

    Em produção, usaríamos um modelo de NLP (ex: HuggingFace Transformers):
        from transformers import pipeline
        nlp = pipeline("sentiment-analysis", model="neuralmind/bert-base-portuguese-cased")
        result = nlp(context[:512])[0]

    Args:
        context (str): Texto ou contexto da notícia

    Returns:
        dict: {"label": str, "score": float, "emoji": str}
    """

    # Simula tempo de inferência do modelo de NLP
    time.sleep(0.5)

    # Possíveis resultados simulados — em produção viria do modelo real
    # Usamos random para variar o resultado a cada nova URL analisada. 
    sentiments = [
        {"label": "Positivo",  "score": round(random.uniform(0.75, 0.97), 2), "emoji": "😊"},
        {"label": "Negativo",  "score": round(random.uniform(0.70, 0.95), 2), "emoji": "😟"},
        {"label": "Neutro",    "score": round(random.uniform(0.60, 0.85), 2), "emoji": "😐"},
        {"label": "Alarmista", "score": round(random.uniform(0.65, 0.90), 2), "emoji": "😰"},
    ]

    return random.choice(sentiments)

```

### providers/rag_provider.py
``` python
# =============================================================================
# providers/rag_provider.py — Recuperação de contexto (RAG simplificado)
#
# Responsabilidade: receber o texto bruto e retornar os trechos mais
# relevantes para alimentar o modelo LLM.
#
# O que é RAG? (Retrieval-Augmented Generation)
#   Em vez de mandar TODO o texto para o modelo (o que pode ser longo e caro),
#   o RAG seleciona apenas os trechos mais relevantes. Na vida real usaríamos
#   embeddings + banco vetorial (ex: FAISS, Chroma). Aqui usamos uma versão
#   simplificada apenas para demonstrar o conceito na pipeline. 
# =============================================================================
 
def run_rag(text: str) -> str:
    """
    Versão simplificada de RAG: seleciona os primeiros N trechos do texto.

    Em uma implementação real, este provider:
      1. Dividiria o texto em chunks de tamanho fixo
      2. Geraria embeddings para cada chunk (ex: sentence-transformers)
      3. Armazenaria em um banco vetorial (FAISS, Chroma, Pinecone...)
      4. Buscaria os chunks mais similares à query do usuário

    Para este projeto educacional, simulamos o passo de "seleção de contexto"
    pegando as primeiras 10 sentenças — que geralmente contêm o lide da notícia.

    Args:
        text (str): Texto bruto extraído pelo scraper

    Returns:
        str: Contexto reduzido a ser enviado ao modelo LLM
    """

    if not text:
        return ""

    # Divide por ponto final e pega as 10 primeiras sentenças
    # Isso simula a "recuperação" dos trechos mais relevantes
    chunks = [chunk.strip() for chunk in text.split(".") if chunk.strip()]
    selected_chunks = chunks[:10]

    # Reconstrói o contexto como texto único
    context = ". ".join(selected_chunks) + "."

    return context

```

### providers/scraper_provider.py
``` python
# =============================================================================
# providers/scraper_provider.py — Extração de texto de páginas web
#
# Responsabilidade: fazer o scraping de uma URL e retornar o texto limpo.
# Esta camada ISOLA a dependência de requests + BeautifulSoup do restante
# da aplicação. Se trocar a lib de scraping, só este arquivo muda.
# =============================================================================

import requests
from bs4 import BeautifulSoup 
 
def scrape_news(url: str) -> str:
    """
    Faz o download e parsing de uma página de notícia.

    Fluxo:
      1. requests.get() → baixa o HTML da URL
      2. BeautifulSoup → faz o parse do HTML
      3. soup.find_all("p") → extrai somente as tags <p> (parágrafos)
      4. Junta tudo em uma única string de texto limpo

    Args:
        url (str): URL completa da notícia (ex: "https://g1.globo.com/...")

    Returns:
        str: Texto completo extraído dos parágrafos da página.
             Retorna string vazia em caso de erro.
    """

    try:
        # Faz a requisição HTTP com timeout de 10 segundos
        response = requests.get(url, timeout=10)

        # Lança exceção se o status HTTP for 4xx ou 5xx
        response.raise_for_status()

        # Parse do HTML com o parser padrão do Python
        soup = BeautifulSoup(response.text, "html.parser")

        # Extrai texto de todas as tags <p> (parágrafos)
        # Essa heurística funciona bem para a maioria dos portais de notícia
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])

        return text

    except requests.exceptions.RequestException as e: 
        return ""

```

### pipelines/news_pipeline.py
``` python
# =============================================================================
# pipelines/news_pipeline.py — Orquestração do fluxo de análise
#
# Responsabilidade: conectar os providers em sequência, formando a pipeline
# completa de processamento de uma notícia.
#
# Este arquivo NÃO conhece Streamlit — é Python puro. Isso facilita testes
# unitários e reaproveitamento da lógica fora do contexto da UI.
#
# Fluxo:
#   URL → [Scraper] → texto bruto
#              ↓
#           [RAG] → contexto reduzido
#              ↓
#    [LLM: resumo + sentimento] → resultado final
# =============================================================================

from providers.scraper_provider import scrape_news
from providers.rag_provider import run_rag
from providers.llm_provider import summarize_text, analyze_sentiment


def analyze_news(url: str, model: str) -> dict:
    """
    Executa a pipeline completa de análise de uma notícia.

    Args:
        url   (str): URL da notícia a ser analisada
        model (str): Modelo LLM selecionado pelo usuário

    Returns:
        dict com as chaves:
            - "article"   (str):  Texto bruto extraído da página
            - "context"   (str):  Contexto selecionado pelo RAG
            - "summary"   (str):  Resumo gerado pelo LLM
            - "sentiment" (dict): Resultado da análise de sentimento
                                  {"label": str, "score": float, "emoji": str}
    """

    # Passo 1: Scraping — faz download e extrai texto da página
    article = scrape_news(url)

    # Passo 2: RAG — seleciona os trechos mais relevantes do texto
    context = run_rag(article)

    # Passo 3a: LLM → gera o resumo da notícia
    summary = summarize_text(context, model)

    # Passo 3b: NLP → analisa o sentimento do texto
    sentiment = analyze_sentiment(context)

    return {
        "article":   article,
        "context":   context,
        "summary":   summary,
        "sentiment": sentiment,
    }
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

    st.title("📋 Histórico de Análises")
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
        key="url_input"    # chave no session_state — lida pelo controller
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
                    value=f"{sentiment['score'] * 100:.0f}%"
                )

            # Barra de progresso visual para o score de confiança
            st.progress(sentiment["score"])

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

@st.cache_data(ttl=3600)
def get_analysis_result(url, model):
    return analyze_news(url=url, model=model)
  
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

    # Validação básica: não executa com URL vazia
    if not url:
        st.warning("Por favor, insira uma URL válida antes de analisar.")
        return

    # Executa a pipeline completa (scraping → RAG → LLM → sentimento) 
    result = get_analysis_result(
        url=url,
        model=st.session_state.model
    )

    # Persiste os resultados no estado da sessão para a page.py renderizar
    st.session_state.article_text = result["article"]
    st.session_state.summary      = result["summary"]
    st.session_state.sentiment    = result["sentiment"]
    st.session_state.current_url  = url


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

