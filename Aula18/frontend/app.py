# =============================================================================
# frontend/app.py — Aula 18: LangChain no front-end
#
# Responsabilidade: app introdutório, num único arquivo, mostrando os três
# conceitos principais do LangChain nesta ordem de complexidade crescente:
#   1) uma "chain" simples (prompt -> modelo -> parser)
#   2) streaming de uma chain no Streamlit
#   3) um agente com tools + visualização do raciocínio (Chain of Thought)
#
# Por ser conteúdo introdutório de uma tecnologia nova, mantemos tudo em um
# único app.py (sem separar em pipeline/providers/features ainda) — assim como
# fizemos nas primeiras aulas de Streamlit e Gradio do Semestre 1.
#
# Como instalar:
#   pip install streamlit langchain langchain-anthropic
# =============================================================================

import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain.agents import create_tool_calling_agent, AgentExecutor

st.set_page_config(page_title="LangChain no Front-end", page_icon="🔗", layout="wide")
st.title("LangChain no Front-end")

modelo = ChatAnthropic(model="claude-haiku-4-5-20251001")


# =============================================================================
# PARTE 1 — UMA CHAIN SIMPLES: prompt | modelo | parser
# =============================================================================
# O operador "|" (pipe) encadeia as etapas: a saída de "prompt" alimenta
# "modelo", que alimenta "parser". É o mesmo espírito da pilha
# UI -> Feature -> Pipeline -> Provider que já usamos, só que dentro de
# uma única expressão do LangChain.
prompt_resumo = ChatPromptTemplate.from_messages([
    ("system", "Você é um analista. Resuma a notícia em 3 pontos principais."),
    ("human", "{texto}"),
])

# StrOutputParser() converte a resposta do modelo (que vem num formato
# especial do LangChain) direto para uma string simples de Python.
chain_resumo = prompt_resumo | modelo | StrOutputParser()


st.header("1. Resumo com streaming")
texto_noticia = st.text_area("Cole a notícia para resumir:")

if st.button("Resumir") and texto_noticia:
    # -------------------------------------------------------------------
    # st.write_stream — NOVO NESTA AULA
    # -------------------------------------------------------------------
    # chain.stream(...) devolve um GERADOR (não a resposta pronta). O
    # st.write_stream consome esse gerador e vai exibindo cada pedaço
    # (token) assim que ele chega — o mesmo padrão de streaming que já
    # vimos no Gradio, na Aula 09 do Semestre 1.
    st.write_stream(chain_resumo.stream({"texto": texto_noticia}))


st.markdown("---")


# =============================================================================
# PARTE 2 — TOOLS: o modelo decide chamar funções externas
# =============================================================================
# @tool transforma uma função Python comum numa "ferramenta" que o modelo
# pode escolher usar. O texto do docstring é o que o modelo lê para decidir
# QUANDO usar essa ferramenta — escreva descrições claras.
@tool
def buscar_cotacao(empresa: str) -> str:
    """Busca a cotação atual de uma empresa na bolsa. Use quando precisar de dados financeiros."""
    # Em produção, aqui chamaríamos uma API real de cotações.
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

prompt_agente = ChatPromptTemplate.from_messages([
    ("system", "Você é um analista financeiro. Use as ferramentas disponíveis para enriquecer sua análise."),
    ("human", "{input}"),
    # "agent_scratchpad" é onde o LangChain registra internamente o
    # raciocínio do agente (quais tools chamou, o que recebeu de volta).
    ("placeholder", "{agent_scratchpad}"),
])

agente = create_tool_calling_agent(modelo, ferramentas, prompt_agente)
executor = AgentExecutor(agent=agente, tools=ferramentas, verbose=False)


# =============================================================================
# PARTE 3 — VISUALIZANDO O RACIOCÍNIO (Chain of Thought) NO FRONT-END
# =============================================================================
# BaseCallbackHandler é a classe base do LangChain para "escutar" eventos
# durante a execução do agente. Sobrescrevemos alguns métodos (on_tool_start,
# on_tool_end, on_agent_action) para capturar cada passo e desenhar na tela
# em tempo real — isto é Transparência (Aula 02 do Semestre 1) aplicada
# a um agente de IA.
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
        self.passos.append(f"Resultado: {output[:200]}")
        self._atualizar()

    def on_agent_action(self, action, **kwargs):
        self.passos.append(f"Decisão: usar `{action.tool}`")
        self._atualizar()

    def _atualizar(self):
        with self.container:
            for passo in self.passos:
                st.markdown(f"- {passo}")


st.header("2. Análise com raciocínio visível")
pergunta = st.text_input("Sua pergunta sobre o mercado:")

if st.button("Analisar") and pergunta:
    col_raciocinio, col_resposta = st.columns([1, 2])

    with col_raciocinio:
        st.markdown("**Raciocínio do modelo:**")
        container_cot = st.container()

    with col_resposta:
        st.markdown("**Resposta final:**")
        placeholder_resposta = st.empty()

    # config={"callbacks": [callback]} é como conectamos nosso "espião"
    # (VisualizadorCoT) à execução do agente.
    callback = VisualizadorCoT(container_cot)
    resultado = executor.invoke(
        {"input": pergunta},
        config={"callbacks": [callback]},
    )

    placeholder_resposta.write(resultado["output"])
