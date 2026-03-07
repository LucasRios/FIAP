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


```

### ui/sidebar.py
``` python
import streamlit as st

def render_sidebar():
    st.sidebar.title("AI News Analyzer")
    
    # Mapeamento Centralizado
    pages = {
        "Analisar notícia": "analysis",
        "Histórico": "history",
        "Configurações": "settings"
    }
    
    choice = st.sidebar.selectbox(
        "Navegação",
        list(pages.keys())
    )
    
    return pages[choice]

```

### state/session.py
``` python
import streamlit as st

def render_sidebar():
    st.sidebar.title("AI News Analyzer")
    
    # Mapeamento Centralizado
    pages = {
        "Analisar notícia": "analysis",
        "Histórico": "history",
        "Configurações": "settings"
    }
    
    choice = st.sidebar.selectbox(
        "Navegação",
        list(pages.keys())
    )
    
    return pages[choice]

```

### providers/llm_provider.py
``` python
import streamlit as st
import time

@st.cache_data
def summarize_text(context, model):

    time.sleep(1)

    return f"Resumo gerado pelo modelo {model} baseado no conteúdo analisado."

```

### providers/rag_provider.py
``` python
import streamlit as st

@st.cache_data
def run_rag(text):

    chunks = text.split(".")[:10]

    context = " ".join(chunks)

    return context

```

### providers/scraper_provider.py
``` python
import requests
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(ttl=3600)
def scrape_news(url):

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    paragraphs = soup.find_all("p")

    text = " ".join([p.get_text() for p in paragraphs])

    return text

```

### pipelines/news_pipeline.py
``` python
from providers.scraper_provider import scrape_news
from providers.rag_provider import run_rag
from providers.llm_provider import summarize_text

def analyze_news(url, model):

    article = scrape_news(url)

    context = run_rag(article)

    summary = summarize_text(context, model)

    return {
        "article": article,
        "summary": summary
    }
```

### features/history/page.py
``` python
import streamlit as st
import pandas as pd

def render():

    st.title("Histórico de análises")

    history = st.session_state.history

    if len(history) == 0:
        st.info("Nenhuma análise registrada.")
        return

    df = pd.DataFrame(history)

    st.subheader("Histórico completo")

    st.dataframe(df)

    st.markdown("---")

    # ==========================
    # Gráfico de feedback
    # ==========================

    if "feedback" in df.columns:

        st.subheader("Distribuição de Feedback")

        feedback_counts = (
            df["feedback"]
            .value_counts()
            .rename_axis("Tipo")
            .reset_index(name="Quantidade")
        )

        feedback_counts = feedback_counts.set_index("Tipo")

        st.bar_chart(feedback_counts)

    st.markdown("---")

    # ==========================
    # Visualizar resumo salvo
    # ==========================

    idx = st.selectbox(
        "Selecionar análise",
        df.index
    )

    st.subheader("Resumo")

    st.write(df.loc[idx]["summary"])
```

### features/news_analysis/page.py
``` python

import streamlit as st
from .controller import run_analysis

def render():

    st.title("Análise de Notícias com IA")

    url = st.text_input(
        "URL da notícia",
        key="url_input"
    )

    st.button(
        "Executar análise",
        on_click=run_analysis
    )

    if not st.session_state.summary:
        st.info("Insira uma URL para iniciar.")
        return

    tab1, tab2  = st.tabs([
        "Resumo",
        "Texto extraído" 
    ])

    with tab1:

        st.subheader("Resumo da notícia")

        placeholder = st.empty()

        text = ""

        for word in st.session_state.summary.split():
            text += word + " "
            placeholder.write(text)

        st.subheader("Feedback")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👍 útil"): 
                st.session_state.history.append({
                    "url": st.session_state.current_url,
                    "summary": st.session_state.summary,
                    "feedback": "positivo"
                })
                st.success("Obrigado pelo feedback!")

        with col2:
            if st.button("👎 ruim"): 
                st.session_state.history.append({
                    "url": st.session_state.current_url,
                    "summary": st.session_state.summary,
                    "feedback": "negativo"
                }) 
                st.error("Obrigado pelo feedback!")           

    with tab2:

        st.subheader("Texto da notícia")

        st.text_area(
            "Conteúdo",
            st.session_state.article_text,
            height=300
        )


```

### features/news_analysis/page.py
``` python
import streamlit as st
from pipelines.news_pipeline import analyze_news

def run_analysis():

    url = st.session_state.url_input

    result = analyze_news(
        url,
        st.session_state.model
    )

    st.session_state.article_text = result["article"]
    st.session_state.summary = result["summary"]
    st.session_state.current_url = url

```

### features/settings/page.py
``` python
import streamlit as st

def render():

    st.title("Configurações")

    st.subheader("Modelo")

    st.selectbox(
        "Escolher modelo",
        ["small", "medium", "large"],
        key="model"
    )

    st.subheader("Parâmetros")

    st.slider(
        "Temperatura",
        0.0,
        1.0,
        key="temperature"
    )

    if st.button("Limpar cache"):

        st.cache_data.clear()

        st.success("Cache limpo.")

```
