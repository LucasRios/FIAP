# Aula 5 — Observabilidade: A IA como Caixa Preta

## Objetivo

Entender o que acontece depois que o usuário clica "Enviar" e por que essa camada invisível importa para o desenvolvedor de front-end. Introduzir o LangSmith como ferramenta de observabilidade para pipelines de IA e mostrar por que esse assunto não é só responsabilidade do back-end.

---

# 1. O Problema que Você Não Vê

Imagine este cenário: seu app está em produção. Os usuários reclamam que "a IA às vezes retorna respostas sem sentido". Você abre o código, não vê nenhum erro. O app não quebra. Os logs mostram `200 OK`. O que está errado?

Sem observabilidade, você não tem como responder:
- Qual texto o usuário enviou?
- Qual prompt exato foi para o modelo?
- O modelo demorou 2s ou 15s nessa chamada?
- Quantos tokens foram usados?
- O resultado foi de boa qualidade ou o modelo "alucionou"?

Essa é a caixa preta da IA: entre o clique do usuário e a resposta na tela, existe um pipeline opaco que você precisa iluminar.

---

# 2. Observabilidade vs. Logging Tradicional

Você provavelmente já ouviu falar em logging. A diferença entre logging tradicional e observabilidade é de profundidade:

| | Logging Tradicional | Observabilidade para IA |
|---|---|---|
| O que captura | Eventos do sistema (`INFO: request received`) | Toda a cadeia de raciocínio do modelo |
| Granularidade | Linha de log | Trace completo (cada passo do pipeline) |
| Tokens | Não | Sim — entrada, saída, custo |
| Latência por etapa | Não | Sim — onde o pipeline é lento |
| Qualidade da resposta | Não | Sim — scores, feedback do usuário |
| Ferramenta | `logging`, `print` | LangSmith, Arize Phoenix, Weights & Biases |

```python
# Logging tradicional — o que você provavelmente tem hoje
import logging

logging.info(f"Usuário enviou texto: {texto[:50]}...")
resultado = modelo.analisar(texto)
logging.info(f"Resultado: {resultado['sentimento']}")
```

Isso diz que algo aconteceu. Não diz **como** aconteceu, quanto custou, se foi lento, ou se o modelo tomou a decisão certa.

---

# 3. O Que Vale Capturar em IA

Para que a observabilidade seja útil, você precisa saber o que registrar. Nem tudo tem o mesmo valor:

**Sobre a entrada:**
- O texto original que o usuário enviou
- O prompt completo construído para o modelo (com contexto, system prompt, exemplos)
- Idioma detectado, tamanho do input, tipo de conteúdo

**Sobre a execução:**
- Qual modelo foi usado (`claude-haiku-4-5-20251001`, `gpt-4o`, etc.)
- Latência total e latência por etapa do pipeline
- Tokens de entrada e tokens de saída
- Custo estimado da chamada

**Sobre a saída:**
- A resposta bruta do modelo
- A resposta processada (após parsing, validação, etc.)
- Se houve fallback para outro modelo
- Se o modelo retornou resposta inválida ou incompleta

**Sobre o usuário:**
- ID de sessão (anonimizado)
- Feedback explícito (like/dislike que construímos na Aula 09 do semestre 1)
- Se o usuário repetiu a mesma pergunta (sinal de que a resposta foi ruim)

---

# 4. Por que Isso é Assunto de Front-end

A pergunta vai aparecer: "Isso não é responsabilidade do back-end?"

Parcialmente sim. Mas o front-end tem informações que o back-end não tem:

**O front-end sabe:**
- Quanto tempo o usuário ficou lendo a resposta
- Se o usuário deu feedback (like/dislike)
- Se o usuário reescreveu a pergunta logo depois
- Em qual parte da interface o usuário clicou após receber a resposta

**O front-end controla:**
- O ID de sessão que vai no header de cada requisição
- Os metadados de contexto que acompanham cada chamada
- A exibição de indicadores de qualidade para o usuário

```python
# O front-end enriquece cada chamada com metadados de contexto
import streamlit as st
import requests
import uuid

# Gera um ID de sessão único ao iniciar o app
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def analisar_com_contexto(texto: str) -> dict | None:
    r = requests.post(
        f"{API_URL}/v1/analise/sentimento",
        json={"texto": texto},
        headers={
            "X-API-Key": API_KEY,
            "X-Session-Id": st.session_state.session_id,  # contexto da sessão
            "X-App-Version": "1.2.0",                     # versão do front
            "X-Feature": "news-analysis",                 # qual feature originou
        },
        timeout=30
    )
    ...
```

O back-end recebe esses headers e os inclui nos traces de observabilidade. Isso conecta o comportamento do usuário com a execução do modelo.

---

# 5. Introdução ao LangSmith

O LangSmith é a ferramenta de observabilidade criada pela equipe do LangChain. Ele captura automaticamente cada chamada ao modelo, monta o trace completo e disponibiliza um dashboard para análise.

O ponto mais importante para entender: **você não precisa usar LangChain para usar LangSmith**. Ele funciona com qualquer SDK de LLM.

```bash
pip install langsmith
```

```python
# Configuração no back-end — variáveis de ambiente
import os
os.environ["LANGCHAIN_API_KEY"] = "sua-chave-langsmith"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "sprint-fiap"
```

Com essas três variáveis configuradas, o LangSmith começa a capturar traces automaticamente quando você usa SDKs compatíveis (Anthropic, OpenAI, LangChain).

---

# 6. Primeiro Trace — Instrumentando uma Chamada

```python
# backend/providers/modelo_provider.py
import anthropic
from langsmith import traceable

client = anthropic.Anthropic()

@traceable(name="analisar_sentimento")
def analisar(texto: str, session_id: str = None) -> dict:
    """
    O decorator @traceable captura automaticamente:
    - Os parâmetros de entrada (texto, session_id)
    - O tempo de execução
    - A resposta do modelo
    - Tokens usados
    - Qualquer exceção
    """
    resposta = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system="Classifique o sentimento do texto como 'positivo', 'negativo' ou 'neutro'. Responda apenas com a palavra.",
        messages=[{"role": "user", "content": texto}]
    )

    sentimento = resposta.content[0].text.strip().lower()

    return {
        "sentimento": sentimento,
        "confianca": 0.9,  # simplificado para o exemplo
        "tokens_usados": resposta.usage.input_tokens + resposta.usage.output_tokens
    }
```

Após a primeira chamada, acesse `https://smith.langchain.com` e veja o trace gerado — input, output, latência, tokens, custo estimado.

---

# 7. O Que o Dashboard Revela

O LangSmith organiza as informações em três visões principais:

**Traces:** cada chamada ao modelo como uma linha do tempo. Você vê cada etapa do pipeline: quanto tempo levou, o que entrou, o que saiu.

**Projects:** agrupa traces por projeto (`sprint-fiap`). Permite comparar a performance de diferentes versões do mesmo pipeline.

**Feedback:** registra avaliações humanas sobre as respostas — o like/dislike que coletamos no front-end pode ser enviado ao LangSmith para criar um dataset de avaliação.

```python
# backend — registrando feedback do usuário no LangSmith
from langsmith import Client

langsmith_client = Client()

def registrar_feedback(run_id: str, aprovado: bool):
    """
    run_id: o ID do trace no LangSmith (retornado na resposta da API)
    aprovado: True se o usuário deu like, False se deu dislike
    """
    langsmith_client.create_feedback(
        run_id=run_id,
        key="aprovacao_usuario",
        score=1.0 if aprovado else 0.0,
    )
```

Na próxima aula vamos instrumentar o pipeline completo do Sprint — não apenas uma função isolada — e explorar o dashboard em tempo real.

---

# Referências

- [LangSmith — Documentação](https://docs.smith.langchain.com)
- [Arize Phoenix](https://phoenix.arize.com)
- [Chip Huyen — Designing Machine Learning Systems (Cap. Monitoring)](https://www.oreilly.com/library/view/designing-machine-learning/9781098107963/)
- [OpenTelemetry para IA](https://opentelemetry.io)
