# =============================================================================
# app.py — Ponto de entrada e orquestrador da aplicação
#
# Responsabilidade: inicializar e lançar o app.
# Este arquivo deve ser o mais fino possível — apenas importa a feature
# e chama .launch(). Ele não contém UI nem lógica de negócio.
#
# Para rodar:
#   pip install gradio
#   python app.py
# =============================================================================

from features.chatbot.page import criar_interface
import gradio as gr

if __name__ == "__main__":
    app = criar_interface()
    app.launch(theme=gr.themes.Soft())
