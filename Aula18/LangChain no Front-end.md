# Aula 7 — LangChain no Front-end

## Objetivo

Introduzir o LangChain como orquestrador de pipelines de IA, entender chains, tools e agents, e mostrar como visualizar o raciocínio do modelo diretamente na interface — transformando a IA de caixa preta em um sistema transparente para o usuário.

---

# 1. O Problema da Transparência

Nas aulas anteriores construímos um pipeline que envia um texto e recebe um resultado. Do ponto de vista do usuário, isso é uma caixa preta — ele não sabe se o modelo leu o texto completo, se considerou as entidades corretas, ou por que chegou àquela conclusão.

Transparência em IA (que estudamos na Aula 02 do semestre 1) não é só sobre mostrar um score de confiança. Em sistemas mais complexos, significa mostrar **como** o modelo chegou à resposta — quais fontes consultou, quais ferramentas usou, qual foi o raciocínio intermediário.

O LangChain foi construído para orquestrar exatamente esse tipo de pipeline — e tem mecanismos nativos para expor cada etapa ao front-end.

---

# 2. O que é LangChain

LangChain é um framework para construir aplicações com LLMs. Ele resolve três problemas:

**Composição:** encadear múltiplas chamadas ao modelo (chains), onde a saída de uma etapa alimenta a entrada da próxima.

**Ferramentas (Tools):** permitir que o modelo decida chamar funções externas — buscar na web, consultar um banco de dados, calcular algo — e usar o resultado na resposta.

**Memória:** manter histórico de conversa entre chamadas, sem precisar gerenciar manualmente o `session_state`.

```bash
pip install langchain langchain-anthropic
```

---

# 3. A Anatomia de uma Chain

Uma chain é uma sequência de etapas onde cada uma transforma a entrada e passa para a próxima. O conceito espelha a arquitetura de pipelines que construímos no semestre 1.

```python
# Uma chain simples: prompt → modelo → parser
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

modelo = ChatAnthropic(model="claude-haiku-4-5-20251001")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um analista de notícias. Seja conciso e objetivo."),
    ("human", "Analise o sentimento da notícia: {texto}")
])

parser = StrOutputParser()

# O operador | encadeia as etapas
chain = prompt | modelo | parser

# Invocar a chain
resultado = chain.invoke({"texto": "A empresa registrou lucro recorde no trimestre."})
print(resultado)  # "positivo"
```

O `|` (pipe) é a sintaxe do LangChain para compor etapas. É direto: a saída de `prompt` alimenta `modelo`, que alimenta `parser`.

---

# 4. Streaming de Chain no Streamlit

Uma das vantagens das chains é o suporte nativo a streaming — você exibe cada token à medida que o modelo os gera, sem esperar a resposta completa.

```python
import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

modelo = ChatAnthropic(model="claude-haiku-4-5-20251001")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um analista. Resuma a notícia em 3 pontos principais."),
    ("human", "{texto}")
])

chain = prompt | modelo | StrOutputParser()

st.title("Análise com Streaming")
texto = st.text_area("Cole a notícia:")

if st.button("Analisar") and texto:
    # st.write_stream recebe um gerador e exibe token a token
    st.write_stream(chain.stream({"texto": texto}))
```

O `chain.stream()` retorna um gerador — exatamente como o padrão de streaming que estudamos no Gradio na Aula 09 do semestre 1. A diferença é que aqui o LangChain gerencia o protocolo de streaming com o modelo.

---

# 5. Tools — O Modelo Usando Ferramentas

Tools permitem que o modelo decida chamar funções externas quando precisar de informações que não tem. Isso transforma um modelo de "gerador de texto" em um agente capaz de agir.

```python
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# Define as ferramentas disponíveis para o modelo
@tool
def buscar_cotacao(empresa: str) -> str:
    """Busca a cotação atual de uma empresa na bolsa. Use quando precisar de dados financeiros."""
    # Em produção, chamaria uma API de cotações
    cotacoes = {"PETR4": "R$ 38,50", "VALE3": "R$ 67,20", "ITUB4": "R$ 32,80"}
    return cotacoes.get(empresa.upper(), f"Cotação de {empresa} não encontrada.")

@tool
def buscar_historico_empresa(empresa: str) -> str:
    """Busca informações históricas sobre uma empresa. Use para contextualizar análises."""
    historicos = {
        "PETR4": "Petrobras — maior empresa de energia do Brasil, fundada em 1953.",
        "VALE3": "Vale — maior mineradora da América Latina, fundada em 1942.",
    }
    return historicos.get(empresa.upper(), f"Histórico de {empresa} não disponível.")

ferramentas = [buscar_cotacao, buscar_historico_empresa]

modelo = ChatAnthropic(model="claude-sonnet-5")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um analista financeiro. Use as ferramentas disponíveis para enriquecer sua análise."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")  # onde o modelo registra seu raciocínio
])

agente = create_tool_calling_agent(modelo, ferramentas, prompt)
executor = AgentExecutor(agent=agente, tools=ferramentas, verbose=True)

resultado = executor.invoke({"input": "Analise as perspectivas da Petrobras para o próximo trimestre."})
print(resultado["output"])
```

Com `verbose=True`, o LangChain imprime cada decisão do agente no terminal — você vê quando ele decidiu chamar `buscar_cotacao`, qual argumento usou, o que recebeu de volta, e como usou essa informação.

---

# 6. Visualizando o Chain of Thought no Front-end

O Chain of Thought (CoT) é o raciocínio intermediário do modelo — os passos que ele percorre antes de dar a resposta final. Mostrar isso ao usuário é uma das formas mais poderosas de transparência.

```python
import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.callbacks import BaseCallbackHandler

# Callback para capturar cada passo do agente
class VisualizadorCoT(BaseCallbackHandler):
    """Captura os eventos do agente e os exibe em tempo real no Streamlit."""

    def __init__(self, container):
        self.container = container
        self.passos = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        nome = serialized.get("name", "ferramenta")
        self.passos.append(f"Consultando **{nome}** com: `{input_str}`")
        self._atualizar()

    def on_tool_end(self, output, **kwargs):
        self.passos.append(f"Resultado: {output[:200]}...")
        self._atualizar()

    def on_agent_action(self, action, **kwargs):
        self.passos.append(f"Decisão: usar `{action.tool}`")
        self._atualizar()

    def _atualizar(self):
        with self.container:
            for passo in self.passos:
                st.markdown(f"- {passo}")


# Interface
st.title("Análise com Raciocínio Visível")
pergunta = st.text_input("Sua pergunta sobre o mercado:")

if st.button("Analisar") and pergunta:
    col_raciocinio, col_resposta = st.columns([1, 2])

    with col_raciocinio:
        st.markdown("**Raciocínio do modelo:**")
        container_cot = st.container()

    with col_resposta:
        st.markdown("**Resposta final:**")
        placeholder_resposta = st.empty()

    # Executa com o callback de visualização
    callback = VisualizadorCoT(container_cot)
    resultado = executor.invoke(
        {"input": pergunta},
        config={"callbacks": [callback]}
    )

    placeholder_resposta.write(resultado["output"])
```

O resultado é uma interface onde o usuário vê, em tempo real, quais ferramentas o modelo consultou e por quê — antes de ver a resposta final. Isso reduz a desconfiança em relação à IA, porque o usuário pode verificar se o raciocínio faz sentido.

---

# 7. Structured Output — Resposta Tipada do Modelo

Em vez de receber um texto livre e tentar parsear, o LangChain permite definir a estrutura exata da resposta usando Pydantic:

```python
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

class AnaliseNoticia(BaseModel):
    sentimento: str = Field(description="'positivo', 'negativo' ou 'neutro'")
    confianca: float = Field(description="Score de 0.0 a 1.0", ge=0.0, le=1.0)
    pontos_principais: list[str] = Field(description="3 pontos principais da notícia")
    recomendacao: str = Field(description="Uma frase de recomendação de ação")

modelo = ChatAnthropic(model="claude-haiku-4-5-20251001")

# with_structured_output garante que a resposta siga o schema Pydantic
modelo_estruturado = modelo.with_structured_output(AnaliseNoticia)

resultado: AnaliseNoticia = modelo_estruturado.invoke(
    "Analise: A empresa registrou crescimento de 30% e anuncia expansão internacional."
)

# Agora você tem um objeto Python tipado — não um dicionário
print(resultado.sentimento)            # "positivo"
print(resultado.confianca)             # 0.92
print(resultado.pontos_principais)     # ["Crescimento de 30%", ...]
```

No Streamlit, renderizar um objeto estruturado é muito mais simples do que parsear um texto livre — você acessa os campos diretamente e sabe o tipo de cada um.

---

# Referências

- [LangChain — Documentação](https://python.langchain.com)
- [LangChain — Tools](https://python.langchain.com/docs/concepts/tools/)
- [LangChain — Streaming](https://python.langchain.com/docs/concepts/streaming/)
- [Anthropic — Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Chain of Thought Prompting — Wei et al., 2022](https://arxiv.org/abs/2201.11903)
