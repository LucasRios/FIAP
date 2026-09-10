# app.py
import os
from dotenv import load_dotenv
from google import genai
from langsmith import traceable, Client
from langsmith.run_helpers import get_current_run_tree

load_dotenv()

gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
langsmith_client = Client()
LANGSMITH_PROJECT = os.environ["LANGSMITH_PROJECT"]


# --- Etapas do pipeline, cada uma como um run filho no trace ---

@traceable(run_type="tool")
def montar_prompt(texto: str) -> str:
    return (
        "Classifique o sentimento do texto como 'positivo', "
        f"'negativo' ou 'neutro'. Responda apenas com a palavra.\n\nTexto: {texto}"
    )


@traceable(run_type="llm")
def chamar_modelo(prompt: str):
    # Usar Chat.send_message (em vez de Models.generate_content) evita o aviso
    # de "Automatic function calling" que o SDK do Gemini emite na chamada direta.
    chat = gemini_client.chats.create(model="gemini-3.5-flash")
    return chat.send_message(prompt)


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
    # `run.session_id` vem None no lado do cliente — o id real do projeto só
    # existe no servidor, depois que o trace foi ingerido. Por isso buscamos o
    # id do projeto pela API (por nome) na hora de gravar o feedback, em vez de
    # tentar tirá-lo do RunTree.
    project_id = langsmith_client.read_project(project_name=LANGSMITH_PROJECT).id

    langsmith_client.create_feedback(
        run_id=run_id,
        session_id=project_id,
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

    # garante que o trace já foi enviado ao LangSmith antes de buscar o projeto
    langsmith_client.flush()

    # simula o usuário clicando em "like" alguns instantes depois
    registrar_feedback(
        run_id=resultado["run_id"],
        aprovado=True,
        comentario="Classificação correta.",
    )