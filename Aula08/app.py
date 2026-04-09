import gradio as gr


def predict_sentiment(text):
    if not text:
        return "Aguardando entrada..."
    return "Positivo" if "bom" in text.lower() else "Negativo"

with gr.Blocks(title="FIAP AI Lab") as demo:
    gr.Markdown("# 🧠 Sentiment Analysis Pro")
    
    with gr.Row():
        input_text = gr.Textbox(
            label="Digite sua frase",
            placeholder="O curso da FIAP é..."
        )
        output_label = gr.Label(label="Resultado")
    
    submit_btn = gr.Button("Analisar")
    
    # Evento principal
    submit_btn.click(
        fn=predict_sentiment,
        inputs=input_text,
        outputs=output_label
    )

    # Evento submit (Enter)
    input_text.submit(
        fn=predict_sentiment,
        inputs=input_text,
        outputs=output_label
    )

    # Examples
    gr.Examples(
        [
            "Este dia está maravilhoso!",
            "Não gostei do atraso."
        ],
        inputs=input_text
    )


demo.launch(pwa=True,share=True)