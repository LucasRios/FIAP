# =============================================================================
# backend/main.py — Aula 24: liberando CORS para apps mobile (Capacitor/Expo)
#
# REAPROVEITADO DA AULA 14/19 — a estrutura do FastAPI com CORSMiddleware já
# existia. O que é NOVO NESTA AULA é a ADIÇÃO de novas origens à lista de
# CORS: agora, além do Streamlit e do Gradio locais, o mesmo back-end
# também precisa aceitar chamadas vindas de apps mobile (Capacitor e Expo).
#
# Contexto: como vimos na Aula 24, o app React Native/Expo chama esta MESMA
# API com fetch() — e o app empacotado com Capacitor roda dentro de uma
# WebView que também pode fazer chamadas diretas via JavaScript. Os dois
# cenários passam pela checagem de CORS do navegador/WebView.
# =============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sprint API", version="1.4.0")

# -----------------------------------------------------------------------------
# ORIGENS PERMITIDAS — NOVO NESTA AULA: as três últimas linhas
# -----------------------------------------------------------------------------
ORIGENS_PERMITIDAS = [
    "http://localhost:8501",              # Streamlit local (Aula 13)
    "http://localhost:7860",              # Gradio local (Aula 14)
    "https://meuapp.streamlit.app",       # Streamlit Cloud (Aula 20)
    "capacitor://localhost",              # NOVO NESTA AULA: app iOS empacotado com Capacitor
    "http://localhost",                   # NOVO NESTA AULA: app Android empacotado com Capacitor
    "exp://192.168.0.10:8081",            # NOVO NESTA AULA: app Expo rodando em modo desenvolvimento
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
# Repare: o back-end é o MESMO das Aulas 1-4. Isso é a separação front/back
# do semestre pagando dividendos — o app mobile consome os mesmos endpoints,
# sem precisarmos duplicar nenhuma lógica de IA.


@app.get("/")
def raiz():
    return {"mensagem": "API de IA - agora também acessível por apps mobile"}
