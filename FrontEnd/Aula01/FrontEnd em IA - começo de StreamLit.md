## 1. O Front-end em IA

Muitos alunos acreditam que front-end é “deixar bonito”. Explique que, em IA, front-end é a diferença entre experimento e produto: um notebook é uma prova de conceito; uma interface transforma hipótese em uso real. Três argumentos centrais:

• Caixa-Preta vs Produto — O notebook mostra comportamento; o produto entrega experiência, documentação, controles, logs e governança. O stakeholder interage, verifica hipóteses e toma decisões.

• Time-to-Market — Em IA a iteração rápida importa mais que otimizações micro-técnicas. Um front-end simples (demo) permite validar hipóteses com usuários não-técnicos em horas/dias, evitando meses de desenvolvimento.

• Ciclo de Feedback (Human-in-the-loop) — Sem interface não há coleta consistente de dados reais: rótulos, correções e sinais de uso. O front-end habilita captura de dados que alimentam retreinamento e melhoria contínua.

Conecte isso à aula: o objetivo não é fazer “UI bonita” por si só, mas construir um produto mínimo que viabilize validação, coleta de sinal e priorização técnica.

---

## 2. O Ecossistema de Ferramentas (20 min)

### Visão geral das principais ferramentas

| Ferramenta | Site oficial | Casos de uso / exemplos reais |
|-----------|--------------|-------------------------------|
| **Streamlit** | https://streamlit.io | Prototipagem rápida de dashboards de IA. Amplamente usado por times de Data Science. Adquirido pela Snowflake para acelerar produtos data-driven. |
| **Gradio** | https://gradio.app | Criação rápida de demos de modelos ML. Muito usado pela Hugging Face para expor modelos públicos. |
| **Dash (Plotly)** | https://dash.plotly.com | Dashboards analíticos corporativos. Utilizado em setores como saúde, finanças e indústria. |
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

Vantagens de começar por Streamlit:

Curva de aprendizado curta: transforma scripts Python diretamente em UI; ideal para formar o hábito de “mostrar o que funciona”.

Scripting linear: a API é orientada a chamadas diretas (st.sidebar, st.columns, st.metric) — ótimo para ensinar arquitetura de app antes de entrar em front-end moderno.

Deploy simples: Cloud/Container/HF Spaces integram bem (rápida validação com stakeholders).

Desafios e gancho para próxima aula (gancho técnico):

Ciclo de re-run: Streamlit reexecuta o script do topo ao fim a cada interação. Se o código não estiver estruturado (caching, separação de funções, controle de estado) o app fica lento. Isso é tópico para a Semana 4 (optimizações, caching, arquitetura reativa).

---
## 4. Anatomia do Streamlit: O Ciclo de Re-run

Explique a diferença chave: em apps web tradicionais o front-end preserva estado no cliente; em Streamlit a execução é sempre retornada ao topo do script e reexecução é controlada por caching e st.session_state. Demonstre com um exemplo mínimo (ver Workshop). Aponte problemas comuns: chamadas bloqueantes (requests/IO) no topo do script, criação de objetos pesados sem cache, loops de IO em cada interação.

---

## 5. Construindo o Dashboard de Métricas de IA

Transformar um script feio (imprime métricas) em um dashboard profissional em Streamlit com sidebar, columns, tabs, métricas, gráficos e logs. Incluir técnicas de performance mínimas (cache, separação de funções).

Requisitos (instalação)
```python
python -m venv .venv
source .venv/bin/activate
pip install streamlit pandas plotly scikit-learn

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
# app_streamlit_step1.py
import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Dashboard IA - Aula 1", layout="wide")

# SIDEBAR - controles globais
with st.sidebar:
    st.header("Configurações")
    modelo = st.selectbox("Modelo", ["bert-v1", "bert-v2", "xgboost-1"])
    dataset = st.selectbox("Dataset", ["v1_clean", "v2_augmented"])
    run = st.button("Rodar avaliação")

# Função que simula métricas (coloque sua lógica real aqui)
@st.cache_data(ttl=60)
def avaliar(modelo, dataset):
    # simula cálculo custoso
    time.sleep(1)
    np.random.seed(hash(modelo+dataset) % 2**32)
    accs = np.cumsum(np.random.rand(10) * 0.01) + 0.85
    losses = np.linspace(0.5, 0.2, 10) + np.random.rand(10)*0.02
    df = pd.DataFrame({"step": list(range(1,11)), "accuracy": accs, "loss": losses})
    return df

# MAIN
st.title("Dashboard de Métricas de IA — Aula 1")
st.subheader(f"Modelo: {modelo} · Dataset: {dataset}")

# KPI em colunas
col1, col2, col3 = st.columns([1,1,2])
df = None
if run:
    df = avaliar(modelo, dataset)
else:
    st.info("Clique em 'Rodar avaliação' na sidebar para gerar métricas.")

if df is not None:
    with col1:
        st.metric("Acurácia (último)", f"{df['accuracy'].iloc[-1]:.3f}",
                  delta=f"{(df['accuracy'].iloc[-1]-df['accuracy'].iloc[0]):+.3f}")
    with col2:
        st.metric("Loss (último)", f"{df['loss'].iloc[-1]:.3f}",
                  delta=f"{(df['loss'].iloc[-1]-df['loss'].iloc[0]):+.3f}")
    with col3:
        st.line_chart(df.set_index("step")[["accuracy","loss"]])

# Tabs
tab1, tab2, tab3 = st.tabs(["Visão Geral","Métricas Detalhadas","Logs"])
with tab1:
    st.write("Resumo rápido da execução")
with tab2:
    st.dataframe(df)
with tab3:
    st.text("Logs de execução (simulados)")
    st.write("- run_id: 1234")
    st.write("- timestamp: 2025-02-04")

```


---
# Referências
- [StreamLit](https://streamlit.io/?utm_source=chatgpt.com)  
- [Gradio](https://gradio.app/?utm_source=chatgpt.com)  
- [Dash.Ploty](https://dash.plotly.com/?utm_source=chatgpt.com)  
- [FastAPI](https://fastapi.tiangolo.com)  
- [Next.JS](https://nextjs.org/?utm_source=chatgpt.com)
- [huggingface](https://huggingface.co/spaces?utm_source=chatgpt.com)

