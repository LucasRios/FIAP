# Aula 16 — Observabilidade: A IA como Caixa Preta

## Objetivo

Entender o que acontece depois que o usuário clica "Enviar" e por que essa camada invisível importa para o desenvolvedor de front-end. Introduzir o LangSmith como ferramenta de observabilidade para pipelines de IA e mostrar por que esse assunto não é só responsabilidade do back-end.

---

# 1. O Problema que Você Não Vê

Imagine este cenário: seu app está em produção. Os usuários reclamam que "a IA às vezes retorna respostas sem sentido". Você abre o código e não vê nenhum erro. O app não quebra. Os logs mostram `200 OK`. O que está errado?

Esse é o núcleo do problema: uma aplicação de IA pode estar tecnicamente saudável — API respondendo, banco funcionando, front-end renderizando normalmente — e ainda assim estar funcionalmente errada. O `200 OK` te diz que a requisição foi processada, mas não te diz se o conteúdo daquela resposta faz sentido. Entre o clique do usuário e o texto que aparece na tela existe um pipeline com várias etapas — construção de prompt, chamada ao modelo, parsing da resposta, validação — e qualquer uma delas pode falhar silenciosamente sem gerar uma exceção.

É aqui que a diferença entre logging tradicional e observabilidade fica clara. Logging tradicional (aquele `logging.info(...)` espalhado pelo código) registra que um evento aconteceu, mas não registra *como* ele aconteceu. Um log como `"Resultado: positivo"` confirma que a função rodou até o fim, mas não guarda o texto exato que o usuário enviou, o prompt completo que foi montado a partir dele, qual modelo respondeu, quanto tempo a chamada levou ou quantos tokens foram consumidos. Se um usuário reclamar que a classificação de sentimento veio errada amanhã, esse log sozinho não ajuda a investigar nada — ele só prova que a função foi chamada.

Observabilidade resolve exatamente essa lacuna: em vez de uma linha de texto solta, ela reconstrói a cadeia de execução inteira de uma chamada — cada etapa do pipeline, o que entrou e o que saiu de cada uma, quanto tempo cada parte levou e, quando aplicável, quantos tokens e qual custo aquela chamada gerou. A pergunta que ela responde não é "a função rodou?", é "**o que exatamente aconteceu dentro dela?**".

---

# 2. O Que Observar e Por Que Isso é Assunto de Front-end

Nem toda informação tem o mesmo valor para investigar um problema, então vale organizar o que faz sentido capturar em quatro grupos. Do lado da entrada, importa guardar o texto original que o usuário digitou, o prompt completo que foi efetivamente enviado ao modelo (já com contexto, system prompt e exemplos incluídos) e características básicas do input, como idioma e tamanho. Do lado da execução, o que mais importa é saber qual modelo respondeu (`gemini-2.0-flash`, `claude-haiku-4-5`, `gpt-4o`...), quanto tempo cada etapa do pipeline levou e quantos tokens de entrada e saída foram consumidos — isso é o que permite responder "por que ficou lento?" ou "quanto essa chamada custou?". Do lado da saída, vale guardar tanto a resposta bruta do modelo quanto a resposta já processada (depois de parsing e validação), porque divergências entre as duas costumam ser exatamente onde o bug mora. E por fim, do lado do usuário, informações como um id de sessão anonimizado e feedback explícito (like/dislike) fecham o quadro, porque conectam a execução técnica com a percepção real de quem usou o produto.

Esse último grupo é o motivo pelo qual observabilidade não é assunto exclusivo do back-end. O back-end sabe o que aconteceu *dentro* do pipeline, mas o front-end sabe coisas que o back-end nunca vê sozinho: quanto tempo o usuário ficou olhando para a resposta antes de agir, se ele deu like ou dislike, se ele reformulou a pergunta logo em seguida (um sinal forte de que a resposta anterior foi ruim) e em que parte da interface ele clicou depois. Além de observar esse comportamento, o front-end também **controla** informações que viajam junto de cada requisição — o id de sessão, a versão do app, qual feature disparou a chamada — e que, se chegarem até a ferramenta de observabilidade, permitem cruzar "o que o modelo fez" com "o que o usuário sentiu sobre isso".

Na prática, isso significa enriquecer cada chamada HTTP com metadados de contexto:

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

O back-end recebe esses headers e os inclui nos traces de observabilidade como `metadata`. É essa ponte que conecta o comportamento do usuário, visível só no front-end, com a execução do modelo, visível só no back-end.

---

# 3. LangSmith em Profundidade

## 3.1 O que é e por que ele existe

O LangSmith é a plataforma de observabilidade criada pela equipe do LangChain. Ele nasceu para resolver exatamente o problema da seção 1: aplicações de IA têm pipelines com várias etapas (prompt → modelo → parsing → validação) e, sem instrumentação, um desenvolvedor não tem como saber em qual etapa uma resposta ruim foi gerada. O LangSmith se conecta ao seu código, captura automaticamente cada chamada relevante, monta a árvore de execução completa (o **trace**) e expõe tudo em um dashboard web.

O ponto mais importante para entender de cara: **você não precisa usar o framework LangChain para usar o LangSmith**. Ele foi desenhado como uma ferramenta de observabilidade independente — funciona com chamadas HTTP cruas, com o SDK da OpenAI, da Anthropic, da Google, ou com qualquer função Python que você queira instrumentar. LangChain é um framework para *construir* pipelines de IA; LangSmith é uma ferramenta para *observar* pipelines de IA, sejam eles construídos com LangChain ou não.

## 3.2 Outras opções do mercado

Vale a pena a turma saber que o LangSmith não é a única opção, porque em um projeto real essa escolha depende do contexto:

| Ferramenta | Característica principal |
|---|---|
| **LangSmith** | Integração mais simples via decorator; tier gratuito generoso; dashboard focado em traces de LLM |
| **Langfuse** | Alternativa open-source (pode ser self-hosted); boa opção quando dados não podem sair da infraestrutura da empresa |
| **Arize Phoenix** | Open-source, forte em avaliação e detecção de drift, roda localmente com poucas dependências |
| **Weights & Biases Weave** | Extensão do W&B (já popular em ML/treinamento) para observabilidade de LLMs |
| **Helicone** | Foco em proxy de API — observa chamadas interceptando o tráfego HTTP, sem precisar de decorators |
| **Datadog / New Relic (LLM Observability)** | Faz sentido quando a empresa já usa essas ferramentas para observabilidade geral e quer tudo no mesmo lugar |
| **OpenTelemetry + backend próprio** | Quando se quer um padrão vendor-neutral e já existe stack de telemetria própria |

Escolhemos LangSmith para o curso por três motivos práticos: tem um tier gratuito suficiente para os exercícios, a instrumentação com decorator é a mais simples de ensinar em pouco tempo, e a documentação é boa. Mas a ideia por trás de qualquer uma dessas ferramentas é a mesma: capturar entrada, saída, latência e metadados de cada etapa de um pipeline de IA.

## 3.3 Conceitos centrais

O LangSmith organiza tudo em uma hierarquia simples:

```text
Project (ex: "sprint-fiap")
   └── Trace (uma execução completa, ex: uma pergunta do usuário)
          ├── Run "gerar_prompt"      (uma etapa)
          ├── Run "chamar_modelo"     (uma etapa, geralmente run_type="llm")
          └── Run "validar_resposta"  (uma etapa)
```

- **Project** — agrupa traces relacionados, normalmente por aplicação ou ambiente (`sprint-fiap-dev`, `sprint-fiap-prod`).
- **Trace** — representa uma operação completa, do início ao fim (ex: uma pergunta do usuário até a resposta final).
- **Run** — cada etapa dentro de um trace. Um trace pode ter vários runs aninhados (um run "pai" chamando runs "filhos"). Cada run tem um `run_type`, que pode ser `chain` (uma etapa lógica qualquer), `llm` (uma chamada a um modelo), `tool` (uma ferramenta/função auxiliar) ou `retriever` (busca de contexto).
- **Feedback** — uma avaliação (humana ou automática) anexada a um run específico, como o like/dislike do usuário.

## 3.4 Como ele funciona junto de qualquer SDK de LLM

Existem dois níveis de integração:

**Nível 1 — `@traceable`, funciona com qualquer coisa.** O decorator `@traceable` do pacote `langsmith` não sabe nada sobre qual SDK de LLM você está usando. Ele simplesmente embrulha a função Python: registra os parâmetros de entrada, mede o tempo de execução, captura o valor de retorno (ou a exceção, se houver) e envia isso para o LangSmith. Como ele opera na camada da sua função, funciona igualmente bem envolvendo uma chamada à OpenAI, à Anthropic, ao Gemini, a um modelo local rodando via Ollama, ou até a uma função que não chama LLM nenhum (como um parser ou uma busca em banco).

**Nível 2 — wrappers de SDK, para instrumentação automática mais rica.** Para os SDKs mais usados, o LangSmith oferece funções como `wrap_openai()` e `wrap_anthropic()`, que envolvem o *client* do SDK (não sua função) e capturam automaticamente detalhes específicos daquele provider — como contagem de tokens, modelo exato usado e parâmetros da chamada — sem que você precise extrair esses campos manualmente. Até o momento não existe um `wrap_gemini()` oficial equivalente; ao usar o SDK do Gemini diretamente, o `@traceable` na sua função ainda captura tudo (input, output, latência), só que informações específicas do provider, como uso de tokens, precisam ser incluídas manualmente no retorno da função, ou lidas do campo `usage_metadata` que a resposta do Gemini já traz. Isso é comum: o Nível 1 sempre funciona como piso; o Nível 2 é um bônus disponível para alguns providers.

Vale mencionar também que, se o pipeline for construído usando o próprio framework LangChain (ex: `ChatGoogleGenerativeAI`, `ChatAnthropic`), o tracing acontece automaticamente sem precisar de `@traceable` nem de wrapper nenhum — mas isso foge do escopo desta aula, que foca em usar o LangSmith de forma independente do LangChain.

## 3.5 Configuração

```bash
pip install langsmith python-dotenv
```

```bash
# .env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=sua-chave-langsmith
LANGSMITH_PROJECT=sprint-fiap
```

> **Atenção:** versões mais antigas da documentação usam `LANGCHAIN_TRACING_V2` e `LANGCHAIN_API_KEY`. Essas variáveis ainda funcionam por compatibilidade, mas a configuração atual e recomendada usa o prefixo `LANGSMITH_`.

- `LANGSMITH_TRACING=true` liga o tracing globalmente. Se for `false` ou a variável não existir, o `@traceable` vira um no-op — a função roda normalmente, só que nada é enviado ao LangSmith. É assim que se desativa observabilidade em testes locais sem tocar no código.
- `LANGSMITH_API_KEY` autentica sua aplicação com a sua conta LangSmith (gerada gratuitamente em `smith.langchain.com`).
- `LANGSMITH_PROJECT` define em qual projeto os traces serão agrupados no dashboard.

Com essas variáveis carregadas no ambiente, qualquer função decorada com `@traceable` já começa a enviar traces — não é preciso nenhuma outra configuração.

---

# 4. Primeiro Trace com Gemini — Passo a Passo

Vamos trocar o exemplo para usar o Gemini, porque a API do Google AI Studio tem um tier gratuito (com limites de requisições por minuto) suficiente para os exercícios da disciplina, sem precisar de cartão de crédito.

## 4.1 Instalação e configuração

```bash
pip install google-genai langsmith python-dotenv
```

```bash
# .env
GEMINI_API_KEY=sua-chave-do-google-ai-studio
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=sua-chave-langsmith
LANGSMITH_PROJECT=sprint-fiap
```

A chave do Gemini é gerada gratuitamente em `aistudio.google.com/apikey`.

## 4.2 O código

```python
# backend/providers/modelo_provider.py
import os
from dotenv import load_dotenv
from google import genai
from langsmith import traceable

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


@traceable(name="analisar_sentimento", run_type="chain")
def analisar(texto: str, session_id: str = None) -> dict:
    resposta = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=texto,
        config={
            "system_instruction": (
                "Classifique o sentimento do texto como 'positivo', "
                "'negativo' ou 'neutro'. Responda apenas com a palavra."
            )
        },
    )

    sentimento = resposta.text.strip().lower()

    return {
        "sentimento": sentimento,
        "tokens_entrada": resposta.usage_metadata.prompt_token_count,
        "tokens_saida": resposta.usage_metadata.candidates_token_count,
    }
```

## 4.3 O que o decorator está fazendo, de fato

`@traceable` não é mágica — é possível descrever exatamente o que ele faz nos bastidores, nesta ordem:

1. **Antes de chamar a função original**, ele cria um objeto de "run" com um `run_id` único e registra: o nome do run (o `name="analisar_sentimento"` que você passou, ou o nome da função se você omitir), o `run_type` (aqui, `"chain"", uma etapa lógica — usaríamos `"llm"` se a própria função fosse a chamada ao modelo), o timestamp de início, e os **argumentos recebidos pela função** (`texto` e `session_id`) como o campo `inputs` do trace.
2. **Ele então chama a função original normalmente**, sem alterar seu comportamento. Do ponto de vista de quem chama `analisar(...)`, nada muda — o decorator é transparente.
3. **Se a função levantar uma exceção**, o decorator captura essa exceção, marca o run como `error`, registra o stack trace como parte do trace, e então relança a exceção normalmente (o chamador ainda precisa tratá-la — o `@traceable` só observa, não engole erros).
4. **Se a função retornar normalmente**, o decorator captura o valor de retorno (o dicionário com `sentimento`, `tokens_entrada`, `tokens_saida`) como o campo `outputs` do trace, e registra o timestamp de término — a diferença entre início e fim vira a **latência** daquele run.
5. **Se, dentro da função decorada, outra função também decorada com `@traceable` for chamada**, o LangSmith detecta automaticamente que aquele novo run é filho do run atual (usando um contexto interno baseado em `contextvars` do Python) e monta a árvore pai-filho sem que você precise passar nenhum id manualmente.
6. **Por fim**, o LangSmith empacota tudo isso (`inputs`, `outputs`, timestamps, `run_type`, hierarquia, `run_id`, e o `metadata`/`tags` que você tiver passado ao decorator) e envia para a API do LangSmith **em uma thread separada, de forma assíncrona** — por isso a instrumentação praticamente não adiciona latência perceptível à sua função original.

Depois de rodar `analisar("Estou muito feliz com o resultado!")` uma vez, o trace aparece em `https://smith.langchain.com`, dentro do projeto `sprint-fiap`, mostrando o texto de entrada, o dicionário de saída, a latência total e os tokens usados.

---

# 5. Registrando Feedback sem o Decorator — o `Client` do LangSmith

O `@traceable` resolve a captura automática *durante* a execução da função, mas o feedback do usuário (like/dislike) acontece **depois** — o usuário só clica em 👍 ou 👎 depois de já ter visto a resposta na tela, quando a função `analisar(...)` já terminou de rodar há muito tempo e o `run` correspondente já foi fechado e enviado ao LangSmith. Não existe como "voltar" e anexar esse feedback usando o decorator, porque o decorator só age no momento em que a função está sendo executada.

A solução é usar o `langsmith.Client()`: um cliente HTTP que fala diretamente com a API do LangSmith, independente de qualquer execução de função. Com ele, dado o `run_id` de um trace que já existe, é possível anexar um feedback a ele a qualquer momento — inclusive em uma requisição HTTP completamente separada, minutos depois.

Para isso funcionar, o `run_id` gerado pelo `@traceable` durante a chamada original precisa ser capturado e devolvido ao front-end, para que o front-end consiga mandá-lo de volta junto com o feedback. Isso é feito com `get_current_run_tree()`, chamado *dentro* da função decorada:

```python
# backend/providers/modelo_provider.py
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

@traceable(name="analisar_sentimento", run_type="chain")
def analisar(texto: str) -> dict:
    resposta = client.models.generate_content(...)
    sentimento = resposta.text.strip().lower()

    run = get_current_run_tree()  # o run que o @traceable acabou de criar

    return {
        "sentimento": sentimento,
        "run_id": str(run.id),  # devolvido para o front-end anexar feedback depois
    }
```

E, em um endpoint separado — chamado bem depois, quando o usuário clica no like/dislike — usamos o `Client` para anexar o feedback:

```python
# backend/routes/feedback.py
from langsmith import Client

langsmith_client = Client()

def registrar_feedback(run_id: str, aprovado: bool, comentario: str | None = None):
    """
    run_id: o id do trace, devolvido pela função analisar() lá na Aula 5
    aprovado: True se o usuário deu like, False se deu dislike
    """
    langsmith_client.create_feedback(
        run_id=run_id,
        key="aprovacao_usuario",
        score=1.0 if aprovado else 0.0,
        comment=comentario,
    )
```

Repare na diferença de papéis: `@traceable` observa a execução enquanto ela acontece; `Client()` edita um trace que já existe, de fora, a qualquer momento depois. São dois mecanismos complementares — o primeiro para captura automática, o segundo para enriquecer um trace já fechado com informação que só existe depois (feedback humano, uma avaliação automática rodada em batch, uma correção manual).

---

# 6. Protótipo Completo

Juntando tudo: configuração via `.env`, uma função de pipeline instrumentada com `@traceable`, e um endpoint de feedback usando `Client`.

```bash
# .env
GEMINI_API_KEY=sua-chave-do-google-ai-studio
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=sua-chave-langsmith
LANGSMITH_PROJECT=sprint-fiap
```

```bash
pip install google-genai langsmith python-dotenv
```

```python
# app.py
import os
from dotenv import load_dotenv
from google import genai
from langsmith import traceable, Client
from langsmith.run_helpers import get_current_run_tree

load_dotenv()

gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
langsmith_client = Client()


# --- Etapas do pipeline, cada uma como um run filho no trace ---

@traceable(run_type="tool")
def montar_prompt(texto: str) -> str:
    return (
        "Classifique o sentimento do texto como 'positivo', "
        f"'negativo' ou 'neutro'. Responda apenas com a palavra.\n\nTexto: {texto}"
    )


@traceable(run_type="llm")
def chamar_modelo(prompt: str):
    return gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )


# --- Pipeline principal: vira o run "pai" no trace ---

@traceable(name="pipeline_analise_sentimento", run_type="chain")
def analisar(texto: str, session_id: str = None) -> dict:
    prompt = montar_prompt(texto)
    resposta = chamar_modelo(prompt)

    sentimento = resposta.text.strip().lower()
    run = get_current_run_tree()  # id do trace, para o feedback ser anexado depois

    return {
        "sentimento": sentimento,
        "tokens_entrada": resposta.usage_metadata.prompt_token_count,
        "tokens_saida": resposta.usage_metadata.candidates_token_count,
        "run_id": str(run.id),
    }


# --- Registro de feedback, desacoplado da execução original ---

def registrar_feedback(run_id: str, aprovado: bool, comentario: str | None = None):
    langsmith_client.create_feedback(
        run_id=run_id,
        key="aprovacao_usuario",
        score=1.0 if aprovado else 0.0,
        comment=comentario,
    )


if __name__ == "__main__":
    resultado = analisar(
        "Estou muito feliz com o resultado do projeto!",
        session_id="sessao-de-teste-001",
    )
    print(resultado)

    # simula o usuário clicando em "like" alguns instantes depois
    registrar_feedback(
        run_id=resultado["run_id"],
        aprovado=True,
        comentario="Classificação correta.",
    )
```

Rodando esse script, o trace `pipeline_analise_sentimento` aparece no LangSmith com dois runs filhos (`montar_prompt` e `chamar_modelo`), cada um com sua própria latência e input/output — e, alguns segundos depois, o feedback `aprovacao_usuario` aparece anexado ao mesmo trace, mesmo tendo sido enviado por uma chamada completamente separada.

Esse é o protótipo que vamos expandir na próxima aula, conectando o pipeline inteiro do Sprint (não apenas uma função isolada) e explorando o dashboard em tempo real.

---

# Referências

- [LangSmith — Documentação](https://docs.smith.langchain.com)
- [LangSmith — Observability Concepts](https://docs.langchain.com/langsmith/observability-concepts)
- [LangSmith — Tracing Quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
- [LangSmith — Log user feedback using the SDK](https://docs.langchain.com/langsmith/attach-user-feedback)
- [Langfuse (alternativa open-source)](https://langfuse.com)
- [Arize Phoenix](https://phoenix.arize.com)
- [Google AI Studio — chaves de API gratuitas](https://aistudio.google.com/apikey)
- [Chip Huyen — Designing Machine Learning Systems (Cap. Monitoring)](https://www.oreilly.com/library/view/designing-machine-learning/9781098107963/)
- [OpenTelemetry para IA](https://opentelemetry.io)
