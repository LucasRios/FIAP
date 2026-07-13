# Aula 0 — Revisão e APIs para Front-enders

## Objetivo

Consolidar o que foi construído no semestre anterior, apresentar o arco do semestre 2 e revisitar os conceitos de API que os alunos já viram em outras disciplinas — desta vez com foco em como o desenvolvedor de front-end de IA os usa no dia a dia.

---

# 1. O que construímos no Semestre 1

O semestre anterior foi uma jornada de dentro para fora: começamos com a tela, aprendemos a dar estado, depois modularizamos, depois autenticamos. A sequência não foi aleatória — ela reflete como um produto de IA real cresce.

| Aula | Tema | O que ficou |
|------|------|-------------|
| 01 | Streamlit — o ecossistema | O ciclo de re-run e por que o front-end de IA não é front-end tradicional |
| 02 | UX para IA | Transparência, latência, incerteza e human-in-the-loop como pilares de design |
| 03 | Estado e callbacks | `st.session_state` como memória da aplicação; widgets como gatilhos, não estado |
| 04 | Visualização de dados | `st.dataframe`, plotly, pydeck, altair — cada biblioteca para uma necessidade |
| 05 | Cache e performance | `st.cache_data` vs `st.cache_resource`, TTL, invalidação manual |
| 06 | Arquitetura modular | Feature-First, pipelines isolados, a pilha UI → Feature → Pipeline → Provider |
| 07 | Autenticação e RBAC | Controle de acesso por perfil, bloqueio real de rotas, session como contrato |
| 08 | Gradio — introdução | Paradigma orientado a eventos vs. re-run do Streamlit; Interface vs. Blocks |
| 09 | Gradio — streaming e UX | Geradores Python como mecanismo de streaming; o "efeito ChatGPT" |
| 10 | Workshop de gráficos | Revisão prática — o que o dado pede, e não o que a ferramenta oferece |

O denominador comum de tudo isso: **o front-end de IA é a camada que torna um modelo utilizável**. Sem ela, o modelo existe apenas para quem escreveu o código.

---

# 2. O que vem no Semestre 2

Se o semestre 1 foi "construir a interface", o semestre 2 é "colocar essa interface no mundo".

Três perguntas vão guiar cada bloco:

**Como o front-end conversa com o back-end?**
Streamlit e Gradio são ótimos para prototipagem, mas em produção o front raramente chama um modelo direto. Ele chama uma API. Vamos entender por que essa separação importa e como implementá-la com FastAPI.

**Como sei o que está acontecendo depois que o usuário clica?**
Latência, tokens consumidos, erros silenciosos — tudo isso vive numa caixa preta sem observabilidade. Vamos instrumentar o pipeline com LangSmith e entender o que o front-end pode (e deve) expor ao usuário.

**Como chego do meu computador até o celular do usuário?**
Docker, deploy em cloud, PWA e as primeiras noções de mobile. O produto de IA não termina no `streamlit run app.py`.

---

# 3. API — Revisão para quem já viu, contexto para quem vai usar

Você já viu API em outras disciplinas. Aqui não vamos reinventar o que foi ensinado — vamos olhar o mesmo conceito com os olhos de quem está construindo o front-end de uma aplicação de IA.

## 3.1 O que é uma API, de verdade

API (Application Programming Interface) é um **contrato entre dois pedaços de software**. Um lado oferece capacidades, o outro as consome — sem precisar saber como o outro foi implementado.

No contexto de IA:

```
Usuário
  ↓
Front-end (Streamlit / Gradio)
  ↓  ← essa seta é uma chamada de API
Back-end (FastAPI com o modelo)
  ↓
Modelo de IA / Banco de Dados
```

O front-end não sabe — e não deve saber — se o modelo é um GPT-4, um BERT local ou uma regressão logística. Ele só sabe o que enviar e o que esperar de volta.

## 3.2 Os Verbos HTTP

HTTP define **métodos** que indicam a intenção da operação. Cada um tem uma semântica clara:

| Verbo | Semântica | Exemplo em IA |
|-------|-----------|---------------|
| `GET` | Ler / buscar um recurso | Buscar o histórico de análises de um usuário |
| `POST` | Criar / enviar dados para processamento | Enviar um texto para o modelo classificar |
| `PUT` | Atualizar um recurso completo | Substituir a configuração de um pipeline |
| `PATCH` | Atualizar parcialmente | Alterar apenas o threshold de confiança |
| `DELETE` | Remover um recurso | Deletar um histórico de conversa |

A regra mais importante para o front-ender: **use o verbo certo**. Um `GET` não deve ter corpo de dados; um `POST` não deve ser usado para buscar coisas. Isso importa porque clientes HTTP (browsers, Streamlit, Gradio) às vezes tratam os verbos de formas diferentes.

## 3.3 Anatomia de uma URL de API

```
https://api.meuapp.com/v1/analise/sentimento?idioma=pt
│       │              │   │      │           └─ query string (parâmetros opcionais)
│       │              │   │      └─ recurso específico
│       │              │   └─ recurso pai
│       │              └─ versão da API
│       └─ host
└─ protocolo
```

Cada parte tem uma responsabilidade:

- **Protocolo** (`https`): segurança da comunicação. Nunca `http` em produção.
- **Host**: onde o servidor vive. Em desenvolvimento local será `localhost:8000`.
- **Versão** (`/v1/`): permite evoluir a API sem quebrar clientes existentes. Você vai criar rotas assim na Aula 03.
- **Recurso**: representa uma entidade ou ação. Prefira substantivos no plural (`/analises`, `/usuarios`), não verbos (`/fazerAnalise`).
- **Query string**: parâmetros opcionais que filtram ou configuram a resposta.

## 3.4 Status Codes — A linguagem de resposta da API

O servidor sempre responde com um número que indica o resultado da operação. Ignorar esse número é um erro comum de quem está começando a consumir APIs.

| Faixa | Significado | Exemplos relevantes |
|-------|-------------|---------------------|
| `2xx` | Sucesso | `200 OK`, `201 Created` |
| `4xx` | Erro do cliente | `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `422 Unprocessable Entity` |
| `5xx` | Erro do servidor | `500 Internal Server Error`, `503 Service Unavailable` |

O `422 Unprocessable Entity` merece atenção especial: o FastAPI o usa quando o corpo da requisição não passa na validação do Pydantic. Você vai ver muito ele na Aula 01.

```python
import requests

resposta = requests.post(
    "http://localhost:8000/v1/analise/sentimento",
    json={"texto": "O produto chegou com defeito."}
)

# Nunca confie que a requisição funcionou sem verificar
if resposta.status_code == 200:
    resultado = resposta.json()
    print(resultado["sentimento"])  # "negativo"
elif resposta.status_code == 422:
    print("Dados inválidos:", resposta.json()["detail"])
else:
    print(f"Erro inesperado: {resposta.status_code}")
```

## 3.5 Headers — O envelope da requisição

Os headers são metadados que viajam junto com a requisição. O front-end de IA usa headers principalmente para três coisas:

**Autenticação:**
```python
headers = {
    "Authorization": "Bearer meu-token-secreto"
}
resposta = requests.get("http://localhost:8000/v1/historico", headers=headers)
```

**Tipo do conteúdo:**
```python
headers = {
    "Content-Type": "application/json"  # o que estou enviando
    "Accept": "application/json"        # o que quero receber
}
```

**Identificação do cliente** (útil para observabilidade, que vamos ver nas Aulas 05 e 06):
```python
headers = {
    "X-Client-Version": "streamlit-app-1.0",
    "X-Session-Id": st.session_state["session_id"]
}
```

## 3.6 Por que API é assunto de front-end

Essa pergunta vai aparecer. A resposta direta:

**Porque o front-end é o cliente da API.**

Não existe "o back-end cuida da API e o front-end só chama". O front-end precisa:

- Saber quais endpoints existem e o que cada um espera
- Tratar erros de forma que o usuário entenda (não expor stack traces)
- Gerenciar autenticação (enviar tokens, lidar com expiração)
- Lidar com latência (mostrar estados de carregamento, não travar a interface)
- Versionar chamadas (quando o back-end muda, o front precisa acompanhar)

Em aplicações de IA isso é ainda mais crítico porque o modelo pode levar segundos para responder, pode retornar resultados probabilísticos que o front precisa interpretar, e pode falhar silenciosamente se o front não verificar a resposta.

---

# 4. O Projeto do Semestre

Durante o semestre 2 vamos evoluir o projeto do Sprint em camadas. A cada bloco de aulas, o que foi construído no semestre anterior vai ganhar uma nova responsabilidade:

```
Semestre 1 — tudo junto
┌─────────────────────────────────────┐
│  Streamlit / Gradio                 │
│  + provider (lógica de IA direta)   │
│  + banco de dados direto            │
└─────────────────────────────────────┘

Semestre 2 — separado e implantado
┌─────────────────┐     ┌─────────────────────┐
│  Streamlit /    │────▶│  FastAPI             │
│  Gradio (front) │     │  (back com modelo)   │
└─────────────────┘     └──────────┬──────────┘
                                   │
                         ┌─────────▼──────────┐
                         │  Banco / Modelo IA  │
                         └────────────────────┘
                         
              ↓ Deploy

         [Docker] → [Cloud] → [Celular]
```

---

# Referências

- [HTTP — MDN Web Docs](https://developer.mozilla.org/pt-BR/docs/Web/HTTP)
- [HTTP Status Codes](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Status)
- [REST API Design — Roy Fielding, 2000](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
- [FastAPI](https://fastapi.tiangolo.com)
- [Requests — Python HTTP Library](https://requests.readthedocs.io)
