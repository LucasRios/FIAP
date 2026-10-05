# =============================================================================
# features/dados_brutos/page.py — Página de dados dos sensores
#
# Expõe criar_pagina(state) — chamada pelo app.py dentro de gr.Column.
# =============================================================================

import gradio as gr
from datetime import datetime

import pipelines.sensor_pipeline as pipeline
import providers.api_provider as eq_provider
from state.app_state import AppState


def criar_pagina(state: AppState) -> None:

    gr.Markdown("## 📡 Dados Brutos dos Sensores")
    gr.Markdown(
        "Leituras convertidas para unidades físicas (V, A, °C, mm/s, RPM). "
        "Ícones de severidade: 🟢 Normal · 🟡 Aviso · 🔴 Crítico  \n"
        "_Limites baseados em ISO 10816 e dados cadastrais do equipamento._"
    )

    # ── Seleção e ações ────────────────────────────────────────────────────
    with gr.Row():
        dropdown   = gr.Dropdown(
            choices=eq_provider.tags_disponiveis(),
            label="Equipamento (TAG)",
            scale=3,
        )
        botao_ler  = gr.Button("⚡ Leitura Atual",  variant="primary",   scale=1)
        botao_hist = gr.Button("📊 Histórico 24h", variant="secondary", scale=1)

    # ── Leitura atual ──────────────────────────────────────────────────────
    gr.Markdown("### Leitura em Tempo Real")
    leitura_md = gr.Markdown(value="_Selecione um equipamento e clique em **⚡ Leitura Atual**._")

    gr.Markdown("---")

    # ── Histórico ──────────────────────────────────────────────────────────
    gr.Markdown("### Histórico de Leituras (últimas 24h)")
    gr.Markdown("_Intervalo de 30 minutos entre amostras — 48 pontos no total._")

    historico_df = gr.Dataframe(
        headers=pipeline.COLUNAS_HISTORICO,
        datatype=["str", "number", "number", "number", "number", "number"],
        interactive=False,
        label="",
    )

    gr.Markdown("---")

    # ── Human-in-the-loop ──────────────────────────────────────────────────
    # O operador registra observações que os sensores sozinhos não capturam.
    # Esses registros alimentarão o dataset de anomalias na Sprint 3.
    gr.Markdown("### 🖊️ Registrar Ocorrência")
    gr.Markdown(
        "Registre comportamentos anômalos observados no campo. "
        "Seu registro alimentará o modelo de detecção de anomalias na Sprint 3."
    )
    with gr.Row():
        input_ocorrencia = gr.Textbox(
            label="Descrição",
            placeholder="Ex: ruído metálico intermitente sob carga máxima...",
            scale=4,
        )
        botao_registrar = gr.Button("📝 Registrar", scale=1)

    msg_ocorrencia = gr.Textbox(label="", interactive=False, show_label=False)

    # ── Eventos ────────────────────────────────────────────────────────────

    botao_ler.click(
        fn=lambda tag: pipeline.leitura_como_markdown(tag) if tag else "_Selecione um equipamento._",
        inputs=dropdown,
        outputs=leitura_md,
    )

    botao_hist.click(
        fn=lambda tag: pipeline.historico_para_tabela(tag) if tag else [],
        inputs=dropdown,
        outputs=historico_df,
    )

    def _registrar(tag: str, descricao: str) -> str:
        # Em produção: persistir via ocorrencia_provider.salvar(tag, descricao)
        if not tag:
            return "❌ Selecione o equipamento antes de registrar."
        if not descricao.strip():
            return "❌ Descreva a ocorrência antes de registrar."
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"✅ Ocorrência registrada para {tag} em {ts}."

    botao_registrar.click(
        fn=_registrar,
        inputs=[dropdown, input_ocorrencia],
        outputs=msg_ocorrencia,
    ).then(fn=lambda: "", outputs=input_ocorrencia)

    # Quando a equipamento navega para cá com uma TAG — carrega automaticamente
    def _carregar_por_estado(tag: str):
        if not tag:
            return gr.update(), "_Selecione um equipamento._", []
        return (
            gr.update(value=tag),
            pipeline.leitura_como_markdown(tag),
            pipeline.historico_para_tabela(tag),
        )

    state.tag_selecionada.change(
        fn=_carregar_por_estado,
        inputs=state.tag_selecionada,
        outputs=[dropdown, leitura_md, historico_df],
    )
