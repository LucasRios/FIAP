## 1. O Front-end em IA

No desenvolvimento tradicional de modelos, o cientista de dados costuma habitar o ecossistema dos notebooks. Embora poderosos para experimentação, os notebooks são ambientes isolados. O Front-end para IA surge não apenas como uma "casca visual", mas como a ponte necessária para transformar um algoritmo em uma solução de negócio.

Sem uma interface, seu modelo é uma "caixa preta": ninguém além de você sabe como ele funciona ou como extrair valor dele. Quando damos uma interface ao usuário, estamos democratizando o acesso à inteligência. Um Front-end bem estruturado permite o Human-in-the-loop, onde o feedback humano em tempo real (corrigindo uma predição, por exemplo) serve de combustível para o retreino e refinamento do modelo. Além disso, uma interface profissional transmite confiança e transparência, elementos cruciais em uma era onde a ética e a explicabilidade da IA são exigências de mercado. 

Três argumentos centrais:

• Caixa-Preta vs Produto — O notebook mostra comportamento; o produto entrega experiência, documentação, controles, logs e governança. O stakeholder interage, verifica hipóteses e toma decisões.

• Time-to-Market — Em IA a iteração rápida importa mais que otimizações micro-técnicas. Um front-end simples (demo) permite validar hipóteses com usuários não-técnicos em horas/dias, evitando meses de desenvolvimento.

• Ciclo de Feedback (Human-in-the-loop) — Sem interface não há coleta consistente de dados reais: rótulos, correções e sinais de uso. O front-end habilita captura de dados que alimentam retreinamento e melhoria contínua.

---

## 2. O Ecossistema de Ferramentas

Cada ferramenta no mercado resolve uma dor específica. Abaixo, detalhamos o panorama atual para que você saiba escolher a "arma" certa para cada batalha.

### Visão geral das principais ferramentas

| Ferramenta | Site oficial | Casos de uso / exemplos reais |
|-----------|--------------|-------------------------------|
| **Streamlit** | https://streamlit.io | Prototipagem rápida de dashboards de IA. Amplamente usado por times de Data Science. Adquirido pela Snowflake para acelerar produtos data-driven. |
| **Gradio** | https://gradio.app | Criação rápida de demos de modelos ML. Muito usado pela Hugging Face para expor modelos públicos. |
| **Dash (Plotly)** | https://dash.plotly.com | Dashboards analíticos corporativos. Utilizado em setores como saúde, finanças e indústria. |
| **Chainlit** | https://chainlit.io/ | LangChain: Frequentemente usada para prototipar agentes que precisam de histórico de chat. |
| **FastAPI** | https://fastapi.tiangolo.com | APIs de inferência de modelos em produção. Base de muitos sistemas de ML escaláveis. |
| **Hugging Face Spaces** | https://huggingface.co/spaces | Hospedagem de demos de IA (Gradio / Streamlit) com fácil compartilhamento. |

### Quando usar cada uma

- **Prova de conceito rápida, demo para stakeholders:** Streamlit, Gradio  
- **Compartilhamento público de modelo / portfolio:** Gradio + Hugging Face Spaces  
- **Dashboards corporativos:** Dash  
- **Dashboard analítico em produção (controle de acesso, escala):** FastAPI + Front-end dedicado   

---

### Exemplos de código — até onde cada ferramenta pode chegar

#### Streamlit — Dashboard simples de métricas
```python
import streamlit as st

st.set_page_config(layout="wide")
st.title("Dashboard de IA")

col1, col2 = st.columns(2)
col1.metric("Acurácia", "0.93", "+0.02")
col2.metric("Loss", "0.21", "-0.04")


st.line_chart({"accuracy": [0.85, 0.88, 0.91, 0.93]})

```

#### Gradio — demo rápida
```python
import gradio as gr

def soma(a,b):
    return a + b

demo = gr.Interface(fn=soma,
                    inputs=[gr.Number(label="A"), gr.Number(label="B")],
                    outputs=gr.Number(label="Soma"),
                    title="Demo Simples - Soma")
if __name__ == "__main__":
    demo.launch()

```
#### Dash — app mínimo
```python

from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

app = Dash(__name__)
df = px.data.iris()
fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")

app.layout = html.Div([
    html.H1("Dash - Demo"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run_server(debug=True)

```

#### Dash — app mínimo
```python

import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    # Onde a mágica do LLM acontece
    await cl.Message(content=f"Recebi seu prompt: {message.content}").send()

```

#### FastAPI (API básica) + Next.js (fetch)
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Metrics(BaseModel):
    accuracy: float
    loss: float

@app.get("/metrics", response_model=Metrics)
async def get_metrics():
    return {"accuracy": 0.92, "loss": 0.15}

```
#### Next.js (exemplo de client)
```JavaScript
import {useEffect, useState} from 'react'

export default function Home() {
  const [m, setM] = useState(null)
  useEffect(() => {
    fetch('http://localhost:8000/metrics')
      .then(r => r.json())
      .then(setM)
  }, [])
  if(!m) return <div>Carregando...</div>
  return <div>Acurácia: {m.accuracy} — Loss: {m.loss}</div>
}
```
---
## 3. Streamlit — explicação e desafios

Escolhemos o Streamlit para iniciar esta jornada por um motivo simples: ele é a linguagem nativa do Cientista de Dados. Ele permite criar interfaces complexas usando apenas Python, sem a necessidade de aprender HTML, CSS ou JavaScript no primeiro momento.

O Poder e o Desafio do "Re-run"
O Streamlit funciona sob um paradigma de execução linear. Sempre que um usuário interage com um botão ou slider, o script inteiro é executado do topo ao fim.

A Vantagem: O estado da tela sempre reflete o estado das suas variáveis de código. É intuitivo.

O Desafio: Imagine que seu modelo de IA demora 30 segundos para carregar. Se o usuário clicar em um botão de "Mudar cor do gráfico", você não quer esperar 30 segundos de novo. Esse é o grande gancho para a nossa Semana 5, onde aprenderemos sobre Caching e Performance para evitar que o app trave.

Deploy simples: Cloud/Container/HF Spaces integram bem (rápida validação com stakeholders).

Ciclo de re-run: Streamlit reexecuta o script do topo ao fim a cada interação. Se o código não estiver estruturado (caching, separação de funções, controle de estado) o app fica lento. Isso é tópico para a Semana 5 (optimizações, caching, arquitetura reativa).

---
## 4. Anatomia do Streamlit: O Ciclo de Re-run

Em apps web tradicionais o front-end preserva estado no cliente; em Streamlit a execução é sempre retornada ao topo do script e reexecução é controlada por caching e st.session_state. 
Problemas comuns: chamadas bloqueantes (requests/IO) no topo do script, criação de objetos pesados sem cache, loops de IO em cada interação.

---

## 5. Construindo o Dashboard de Métricas de IA

Transformando um script feio (imprime métricas) em um dashboard profissional em Streamlit com sidebar, columns, tabs, métricas, gráficos e logs. Incluir técnicas de performance mínimas (cache, separação de funções).

Requisitos (instalação)
```python
python -m venv venv
```

```python
python -m pip install streamlit
# Criar o arquivo
touch app.py
```

O Ponto de Partida (o “script feio”)
```python
# script_feio.py
import random
import time

def avaliar():
    time.sleep(1)  # simula inferência
    return {"accuracy": random.uniform(0.6, 0.98),
            "loss": random.uniform(0.1, 0.6)}

if __name__ == "__main__":
    print("Avaliando modelo...")
    m = avaliar()
    print("accuracy:", m["accuracy"])
    print("loss:", m["loss"])

```

Estruturando com st.sidebar, st.columns, st.tabs

- Sidebar: seleção de modelo/versão/dataset (controles globais).
- Main: título, KPIs principais (usando st.metric) e gráficos (linha de tendência).
- Tabs: Visão Geral / Métricas Detalhadas / Logs.

```python
#importa o streamLit para podermos seguir com a programação normal no collab
import streamlit as st


#title para definir o título da interface
st.title("Minha IA em Bloquinhos")


#1 - Pense em abas para agrupar dados de contextos diferentes
aba1, aba2 = st.tabs(["Interação", "Métricas da IA"])

#construa cada aba com seu contexto
with aba1:
    #2 - dentro de cada aba pense em linhas
    st.header("Entrada de Dados")    

    # 3 - dentro de cada linha pense em colunas
    col1, col2 = st.columns(2)
    with col1:
        st.file_uploader("Suba sua imagem")
    with col2:
        st.text_input("Comando para a IA")
    
    if st.button("Executar Modelo"):
        st.info("Aqui apareceria a resposta do modelo!")

with aba2:
    st.header("Performance")
    st.metric(label="Confiança", value="98%", delta="2%")
 
```

O mesmo código rodando no Collab

```python

#instalar o Streamlit e o cloudflared (que vai "expor" o servidor do Colab para a internet)
!pip install -q streamlit
!wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb

```

```python

#Escreve o app.py no collab para poder ter uma interface
%%writefile app.py

#importa o streamLit para podermos seguir com a programação normal no collab
import streamlit as st


#title para definir o título da interface
st.title("Minha IA em Bloquinhos")


#1 - Pense em abas para agrupar dados de contextos diferentes
aba1, aba2 = st.tabs(["Interação", "Métricas da IA"])

#construa cada aba com seu contexto
with aba1:
    #2 - dentro de cada aba pense em linhas
    st.header("Entrada de Dados")    

    # 3 - dentro de cada linha pense em colunas
    col1, col2 = st.columns(2)
    with col1:
        st.file_uploader("Suba sua imagem")
    with col2:
        st.text_input("Comando para a IA")
    
    if st.button("Executar Modelo"):
        st.info("Aqui apareceria a resposta do modelo!")

with aba2:
    st.header("Performance")
    st.metric(label="Confiança", value="98%", delta="2%")

```

```python

import subprocess
import threading
import time

def run_streamlit():
    # Roda o streamlit na porta 8501
    subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501"])

def run_tunnel():
    # Cria o túnel da Cloudflare
    p = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:8501"], 
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in p.stdout:
        if ".trycloudflare.com" in line:
            print("\n--- SEU APP ESTÁ RODANDO NO LINK ABAIXO ---")
            print(line.split("https://")[1].strip().split(" ")[0])
            print("-------------------------------------------\n")

# Inicia o Streamlit em uma thread e o túnel em outra
threading.Thread(target=run_streamlit).start()
time.sleep(5)
run_tunnel()

```

---
# Referências
- [StreamLit](https://streamlit.io/?utm_source=chatgpt.com)  
- [Gradio](https://gradio.app/?utm_source=chatgpt.com)  
- [Dash.Ploty](https://dash.plotly.com/?utm_source=chatgpt.com)  
- [FastAPI](https://fastapi.tiangolo.com)  
- [Next.JS](https://nextjs.org/?utm_source=chatgpt.com)
- [huggingface](https://huggingface.co/spaces?utm_source=chatgpt.com)




