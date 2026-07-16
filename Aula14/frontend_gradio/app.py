# =============================================================================
# frontend_gradio/app.py — Aula 14: Gradio consumindo FastAPI de forma async
#
# Responsabilidade: interface Gradio que chama o back-end FastAPI (Aulas 12-13)
# usando httpx assíncrono, em vez do requests síncrono usado no Streamlit.
#
# NOVO NESTA AULA: o uso de async/await e da biblioteca httpx. O restante
# (Blocks, Textbox, Button) já é familiar desde a Aula 08 do Semestre 1.
#
# Como instalar:
#   pip install gradio httpx
#
# Como rodar (com o back-end da Aula 12/13 rodando em outro terminal):
#   python app.py
# =============================================================================

import gradio as gr
import httpx  # NOVO NESTA AULA: cliente HTTP assíncrono, alternativa ao requests

API_URL = "http://localhost:8000"
API_KEY = "minha-chave"  # em produção, viria de uma variável de ambiente


# -----------------------------------------------------------------------------
# POR QUE ASYNC IMPORTA AQUI — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# Um modelo de IA pode levar vários segundos para responder. Se a função fosse
# síncrona (como no requests.post), o processo Python inteiro ficaria parado
# esperando — nenhum outro usuário conseguiria ser atendido nesse meio tempo.
#
# "async def" + "await" dizem ao Python: "enquanto espera a rede responder,
# libere o processo para fazer outras coisas". Isso é essencial quando vários
# usuários usam o app Gradio ao mesmo tempo.
async def analisar_texto_async(texto: str) -> tuple[str, float]:
    """
    Função assíncrona chamada pelo Gradio quando o usuário clica em Analisar.

    Args:
        texto: o texto digitado pelo usuário no Textbox.

    Returns:
        Uma tupla (sentimento, confianca) — o Gradio distribui cada valor
        para o componente de saída correspondente, na ordem definida em
        outputs=[...] mais abaixo.
    """
    # "async with" garante que a conexão HTTP seja fechada corretamente
    # no final, mesmo se der erro no meio do caminho.
    async with httpx.AsyncClient() as client:
        resposta = await client.post(
            f"{API_URL}/v1/analise/sentimento",
            json={"texto": texto},
            headers={"X-API-Key": API_KEY},
            timeout=10.0,
        )

    if resposta.status_code == 200:
        dados = resposta.json()
        return dados["sentimento"], dados["confianca"]

    # Em caso de erro, devolvemos uma mensagem amigável nos próprios
    # componentes de saída, em vez de deixar a exceção estourar na tela.
    return f"Erro {resposta.status_code}", 0.0


# -----------------------------------------------------------------------------
# INTERFACE GRADIO (Blocks) — mesmo padrão da Aula 08
# -----------------------------------------------------------------------------
with gr.Blocks(title="Análise de Sentimento (async)") as demo:
    gr.Markdown("## Análise de Sentimento via FastAPI (chamada assíncrona)")

    with gr.Row():
        entrada = gr.Textbox(label="Texto", lines=4)

    with gr.Row():
        sentimento = gr.Textbox(label="Sentimento")
        confianca = gr.Number(label="Confiança")

    botao = gr.Button("Analisar")

    # O Gradio detecta automaticamente que analisar_texto_async é uma
    # função "async def" e sabe executá-la corretamente — não precisamos
    # fazer nada especial aqui além de passar a função normalmente.
    botao.click(
        fn=analisar_texto_async,
        inputs=[entrada],
        outputs=[sentimento, confianca],
    )


if __name__ == "__main__":
    demo.launch()
