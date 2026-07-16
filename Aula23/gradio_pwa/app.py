# =============================================================================
# gradio_pwa/app.py — Aula 23: transformando o Gradio em PWA
#
# Responsabilidade: mesma ideia do streamlit_pwa/app.py, mas o Gradio tem
# suporte NATIVO para customizar o <head> da página via o parâmetro head=
# do gr.Blocks — não precisamos de nenhum truque de injeção de HTML.
#
# NOVO NESTA AULA: o parâmetro head=cabecalho_pwa. O restante (Blocks,
# Markdown) já é familiar desde a Aula 08 do Semestre 1.
#
# Como instalar:
#   pip install gradio
# =============================================================================

import gradio as gr

# -----------------------------------------------------------------------------
# CABEÇALHO PWA — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# Este bloco de HTML é injetado direto no <head> da página pelo próprio
# Gradio. Cada tag tem um papel:
#   - manifest: diz ao navegador como instalar o app
#   - theme-color / apple-mobile-web-app-*: comportamento em tela cheia no iOS
#   - apple-touch-icon: o ícone usado quando adicionado à tela inicial no iOS
#   - o <script>: registra o service worker, igual fizemos no Streamlit
cabecalho_pwa = """
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#FF4B4B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Análise de IA">
<link rel="apple-touch-icon" href="/icone-192.png">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
"""

with gr.Blocks(
    title="Análise de IA",
    head=cabecalho_pwa,
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown("## Análise de Notícias — instalável como app")
    gr.Markdown(
        "Este Space agora é um PWA: pode ser adicionado à tela inicial "
        "do celular como se fosse um app nativo."
    )

    entrada = gr.Textbox(label="Texto para análise", lines=4)
    saida = gr.Textbox(label="Resultado")

    def analisar_exemplo(texto: str) -> str:
        # Exemplo introdutório — aqui entraria a chamada à API (Aula 14).
        return "Exemplo: sentimento positivo (fluxo real na Aula 14)."

    gr.Button("Analisar").click(fn=analisar_exemplo, inputs=[entrada], outputs=[saida])


if __name__ == "__main__":
    demo.launch()
