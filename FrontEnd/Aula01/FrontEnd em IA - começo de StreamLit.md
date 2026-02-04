# Aula 1 — O Rosto da Inteligência

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
# Referências
- [StreamLit](https://streamlit.io/?utm_source=chatgpt.com)  
- [Gradio](https://gradio.app/?utm_source=chatgpt.com)  
- [Dash.Ploty](https://dash.plotly.com/?utm_source=chatgpt.com)  
- [FastAPI](https://fastapi.tiangolo.com)  
- [Next.JS](https://nextjs.org/?utm_source=chatgpt.com)
- [huggingface](https://huggingface.co/spaces?utm_source=chatgpt.com)
