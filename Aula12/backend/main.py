# =============================================================================
# ARQUIVO: backend/main.py — Aula 12: FastAPI, Do Python Simples ao Backend de IA
# =============================================================================
# Responsabilidade: este é o PRIMEIRO servidor de back-end do semestre.
# Até aqui (Semestre 1), o Streamlit/Gradio chamava o "provider" (a IA) direto,
# dentro do mesmo processo Python. A partir de hoje, essa lógica passa a viver
# aqui, num servidor separado, que qualquer front-end pode chamar via HTTP.
#
# TUDO NESTE ARQUIVO É NOVO NESTA AULA — é o nosso primeiro contato com FastAPI.
#
# Como instalar (rode no terminal, dentro da pasta backend/):
#   pip install fastapi uvicorn pydantic
#
# Como rodar o servidor:
#   uvicorn main:app --reload
#
# Depois de rodar, abra no navegador:
#   http://localhost:8000        -> resposta em JSON
#   http://localhost:8000/docs   -> documentação interativa (Swagger UI)
# =============================================================================

from fastapi import FastAPI
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# 1) CRIANDO O APP FASTAPI
# -----------------------------------------------------------------------------
# "app" é o objeto principal do FastAPI. É nele que penduramos todas as rotas
# (endpoints) do nosso servidor. Pense nele como o "st" do Streamlit: o objeto
# central que representa a aplicação inteira.
app = FastAPI(
    title="API de IA - FIAP",   # aparece no topo da documentação /docs
    version="1.0.0",
)


# -----------------------------------------------------------------------------
# 2) A ROTA MAIS SIMPLES POSSÍVEL
# -----------------------------------------------------------------------------
# @app.get("/") é um "decorator" — ele diz ao FastAPI: "quando alguém fizer uma
# requisição GET para a URL raiz (/), execute a função abaixo".
# A função apenas retorna um dicionário Python; o FastAPI converte isso
# automaticamente para JSON. Não precisamos fazer nenhuma conversão manual.
@app.get("/")
def raiz():
    return {"mensagem": "API de IA funcionando"}


# -----------------------------------------------------------------------------
# 3) PYDANTIC — VALIDAÇÃO DE DADOS QUE VEM DE GRAÇA
# -----------------------------------------------------------------------------
# Uma classe que herda de BaseModel descreve o "formato" esperado dos dados.
# Cada atributo vira um campo obrigatório (ou opcional, se tiver valor padrão).
# O FastAPI usa essa classe para validar automaticamente o que o cliente envia
# — se vier um campo errado ou faltando, o cliente recebe um erro 422 claro,
# sem precisarmos escrever nenhuma validação manual (tipo if/else).

class EntradaAnalise(BaseModel):
    texto: str               # obrigatório: o texto que o usuário quer analisar
    idioma: str = "pt"       # opcional: assume "pt" se não for enviado
    max_tokens: int = 512    # opcional: limite de tokens da resposta do modelo


class ResultadoAnalise(BaseModel):
    sentimento: str          # "positivo", "negativo" ou "neutro"
    confianca: float         # um número entre 0.0 e 1.0
    tokens_usados: int       # quantos tokens a chamada consumiu


# -----------------------------------------------------------------------------
# 4) UM ENDPOINT QUE RECEBE DADOS (POST) E OS VALIDA COM PYDANTIC
# -----------------------------------------------------------------------------
# response_model=ResultadoAnalise diz ao FastAPI qual é o formato da resposta.
# Isso também aparece automaticamente na documentação /docs.
#
# Repare que a função recebe "entrada: EntradaAnalise" como parâmetro — o
# FastAPI lê o corpo (body) da requisição, valida com a classe EntradaAnalise
# e só então chama esta função. Se a validação falhar, a função nem é chamada.
@app.post("/v1/analise/sentimento", response_model=ResultadoAnalise)
def analisar_sentimento(entrada: EntradaAnalise):
    # Em um projeto real, aqui entraria a chamada ao modelo de IA de verdade
    # (como veremos na Aula 15, quando ligarmos isso ao provider do Sprint).
    # Por enquanto, simulamos uma resposta simples só para praticar o formato.
    sentimento_simulado = "negativo" if "defeito" in entrada.texto.lower() else "positivo"

    return ResultadoAnalise(
        sentimento=sentimento_simulado,
        confianca=0.87,
        tokens_usados=len(entrada.texto.split())  # aproximação simples: 1 palavra = 1 token
    )


# -----------------------------------------------------------------------------
# 5) PARÂMETROS DE PATH E QUERY STRING
# -----------------------------------------------------------------------------
# Nem todo dado vai no corpo da requisição. O FastAPI reconhece automaticamente
# três tipos de parâmetro pela forma como você escreve a função:

# 5a) Parâmetro de PATH — faz parte da própria URL e é sempre obrigatório.
# Exemplo de chamada: GET /v1/analise/42
@app.get("/v1/analise/{analise_id}")
def buscar_analise(analise_id: int):
    # analise_id chega aqui já convertido para int pelo FastAPI.
    # Se alguém chamar /v1/analise/abc (não é número), o FastAPI já barra
    # a requisição com um erro 422 antes mesmo de entrar nesta função.
    return {"id": analise_id, "texto": "..."}


# 5b) Parâmetros de QUERY STRING — vêm depois do "?" na URL e são opcionais
# quando têm um valor padrão (como pagina=1 e tamanho=10 abaixo).
# Exemplo de chamada: GET /v1/historico?pagina=2&tamanho=5
@app.get("/v1/historico")
def listar_historico(pagina: int = 1, tamanho: int = 10):
    return {"pagina": pagina, "tamanho": tamanho}


# -----------------------------------------------------------------------------
# O que fazer a seguir (fora deste arquivo, no terminal):
#
#   uvicorn main:app --reload
#
# --reload faz o servidor reiniciar sozinho sempre que você salvar o arquivo
# — muito útil durante o desenvolvimento (é como o "re-run" automático do
# Streamlit, mas para o back-end).
# =============================================================================
