# =============================================================================
# features/chatbot/page.py — Interface do chatbot
#
# Responsabilidade: APENAS UI.
# Esta camada coleta input, chama o pipeline e exibe resultados.
# Ela não sabe nada sobre modelos, APIs ou onde o feedback é salvo.
#
# Regra: se você encontrar lógica de negócio aqui, ela pertence ao pipeline.
# =============================================================================

import gradio as gr

import pipelines.chat_pipeline as pipeline


def criar_interface() -> gr.Blocks:
    """
    Constrói e retorna o objeto gr.Blocks com toda a interface do chatbot.

    Retorna o app sem chamá-lo — quem faz o .launch() é o app.py.
    Isso permite que o mesmo componente seja montado em diferentes contextos
    (desenvolvimento local, testes, embed em app maior).
    """

    with gr.Blocks(title="AI Chatbot com Streaming e Feedback") as app:

        # ── Estado interno ──────────────────────────────────────────────────
        # gr.State é o equivalente ao st.session_state do Streamlit.
        # Persiste valores entre eventos sem rerun completo.
        # Usamos dois estados separados porque pergunta e resposta são
        # capturados em momentos diferentes do fluxo de eventos.
        estado_ultima_pergunta = gr.State("")
        estado_ultima_resposta = gr.State("")

        # ── Cabeçalho ───────────────────────────────────────────────────────
        gr.Markdown("# 🤖 Chatbot com Streaming, Confiança e Feedback Humano")
        gr.Markdown(
            "Este app demonstra os quatro pilares de UX para IA vistos na Aula 02, "
            "agora aplicados a um modelo generativo com Gradio:\n\n"
            "**Transparência** · **Gestão de Incerteza** · **Design para Latência** · **Human-in-the-loop**"
        )
        gr.Markdown("---")

        # ── Layout principal: chat à esquerda, painel à direita ─────────────
        with gr.Row():

            # ── Coluna esquerda: conversa ───────────────────────────────────
            with gr.Column(scale=3):
                gr.Markdown("### 💬 Conversa")

                chatbot = gr.Chatbot(
                    label="Histórico",
                    height=400
                )

                with gr.Row():
                    input_mensagem = gr.Textbox(
                        label="",
                        placeholder="Digite sua mensagem e pressione Enter...",
                        scale=4,
                        container=False
                    )
                    botao_enviar = gr.Button("Enviar ➤", variant="primary", scale=1)

                botao_limpar = gr.Button("🗑️ Limpar conversa", variant="secondary")

            # ── Coluna direita: confiança + feedback ────────────────────────
            with gr.Column(scale=2):

                # Pilar: Gestão de Incerteza
                gr.Markdown("### 📊 Gestão de Incerteza")
                output_confianca_texto = gr.Textbox(
                    label="Análise de Confiança",
                    lines=2,
                    interactive=False,
                    value="Aguardando resposta..."
                )
                output_nivel = gr.Textbox(
                    label="Nível",
                    interactive=False,
                    value=""
                )

                gr.Markdown("---")

                # Pilar: Human-in-the-loop
                gr.Markdown("### 👥 Human-in-the-loop")
                gr.Markdown(
                    "Avalie a última resposta. "
                    "Seu feedback é registrado para retreinamento do modelo."
                )

                with gr.Row():
                    botao_like = gr.Button("👍 Resposta correta", variant="secondary")
                    botao_dislike = gr.Button("👎 Resposta incorreta", variant="secondary")

                output_feedback_status = gr.Textbox(
                    label="Status do Feedback",
                    interactive=False,
                    value=""
                )

                gr.Markdown("---")

                # Pilar: Transparência — exemplos ajudam o usuário a entender
                # o espaço de entrada e reduzem o atrito inicial
                gr.Markdown("### 💡 Exemplos para testar")
                gr.Examples(
                    examples=[
                        ["Explique o conceito de streaming em interfaces de IA"],
                        ["O que é human-in-the-loop e por que é importante?"],
                        ["Como funciona o sistema de confiança deste app?"],
                        ["Oi"],  # pergunta curta → confiança baixa simulada
                    ],
                    inputs=input_mensagem,
                    label=""
                )

        # ── Conexão de eventos ──────────────────────────────────────────────
        # Cada evento conecta um componente de UI a uma função do pipeline.
        # A UI não implementa lógica — apenas orquestra chamadas.
        #
        # O encadeamento .then() permite executar ações em sequência após
        # o streaming terminar: guardar a pergunta no estado, limpar o input.

        def _enviar(mensagem, historico):
            """Delega inteiramente ao pipeline — a UI não processa nada."""
            yield from pipeline.processar_mensagem(mensagem, historico)

        # Evento: clique no botão Enviar
        botao_enviar.click(
            fn=_enviar,
            inputs=[input_mensagem, chatbot],
            outputs=[chatbot, output_confianca_texto, output_nivel, estado_ultima_resposta],
        ).then(
            fn=lambda msg: msg,          # captura a pergunta antes de limpar o input
            inputs=input_mensagem,
            outputs=estado_ultima_pergunta
        ).then(
            fn=lambda: "",               # limpa o campo de texto após envio
            outputs=input_mensagem
        )

        # Evento: Enter no campo de texto (mesmo fluxo do botão)
        input_mensagem.submit(
            fn=_enviar,
            inputs=[input_mensagem, chatbot],
            outputs=[chatbot, output_confianca_texto, output_nivel, estado_ultima_resposta],
        ).then(
            fn=lambda msg: msg,
            inputs=input_mensagem,
            outputs=estado_ultima_pergunta
        ).then(
            fn=lambda: "",
            outputs=input_mensagem
        )

        # Evento: feedback positivo
        botao_like.click(
            fn=lambda p, r: pipeline.registrar_feedback(p, r, "positivo"),
            inputs=[estado_ultima_pergunta, estado_ultima_resposta],
            outputs=output_feedback_status
        )

        # Evento: feedback negativo
        botao_dislike.click(
            fn=lambda p, r: pipeline.registrar_feedback(p, r, "negativo"),
            inputs=[estado_ultima_pergunta, estado_ultima_resposta],
            outputs=output_feedback_status
        )

        # Evento: limpar conversa — reseta todos os componentes ao estado inicial
        botao_limpar.click(
            fn=lambda: ([], "Aguardando resposta...", "", ""),
            outputs=[chatbot, output_confianca_texto, output_nivel, output_feedback_status]
        )

    return app
