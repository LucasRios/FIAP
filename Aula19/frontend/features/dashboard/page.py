# =============================================================================
# features/dashboard/page.py — Dashboard Operacional (Sprint 2)
#
# Expõe criar_pagina(state) — chamada pelo app.py dentro de gr.Column.
#
# O que esta página entrega (Sprint 2):
#   ✅ Navegação por Planta / Área / Equipamento (hierarquia física)
#   ✅ Cards de telemetria em tempo real com cores semânticas
#   ✅ Gráficos de série temporal das últimas 24h (Plotly)
#   ✅ Placa de identificação simulada do motor
#
# Fluxo de uso:
#   1. Usuário seleciona Planta → dropdown de Áreas se atualiza
#   2. Usuário seleciona Área  → dropdown de Equipamentos se atualiza
#   3. Usuário seleciona TAG   → cards, gráfico e placa carregam automaticamente
#   4. Botão "Atualizar" recarrega a leitura atual (nova amostra simulada)
#
# Este arquivo NÃO conhece banco de dados — toda lógica fica nos pipelines.
# =============================================================================

import gradio as gr

import providers.api_provider        as planta_provider
import pipelines.dashboard_pipeline  as pipeline
from state.app_state import AppState


def criar_pagina(state: AppState) -> None:

    gr.Markdown("## 📊 Dashboard Operacional")
    gr.Markdown(
        "Selecione a localização do ativo para monitorar seu estado em tempo real. "
        "🟢 Normal · 🟡 Aviso · 🔴 Crítico"
    )

    # ── Seção 1: Navegação por Planta / Área / Equipamento ──────────────────
    #
    # Por que três dropdowns em cascata?
    # Em plantas industriais reais, há dezenas ou centenas de motores.
    # Navegar pela hierarquia (Planta → Área → TAG) é mais rápido do que
    # rolar uma lista gigante de TAGs.
    #
    gr.Markdown("### 🗺️ Localização do Ativo")

    with gr.Row():
        dd_planta = gr.Dropdown(
            choices=planta_provider.listar_plantas(),
            label="Planta",
            scale=1,
            info="Instalação industrial",
        )
        dd_area = gr.Dropdown(
            choices=[],
            label="Área",
            scale=1,
            info="Setor ou linha de produção",
        )
        dd_equip = gr.Dropdown(
            choices=[],
            label="Equipamento (TAG)",
            scale=1,
            info="TAG de identificação do motor",
        )
        botao_atualizar = gr.Button("🔄 Atualizar Leitura", variant="primary", scale=1)

    gr.Markdown("---")

    # ── Seção 2: Telemetria em Tempo Real ────────────────────────────────────
    #
    # Cards com a leitura mais recente de cada sensor.
    # O ícone de alerta muda automaticamente conforme os limites operacionais.
    #
    gr.Markdown("### 📡 Telemetria em Tempo Real")

    cards_md = gr.Markdown(
        value="_Selecione um equipamento para exibir a telemetria._"
    )

    gr.Markdown("---")

    # ── Seção 3: Gráficos de Série Temporal (últimas 24h) ────────────────────
    #
    # Permite ao operador identificar tendências e anomalias que uma leitura
    # pontual não revelaria. Ex: temperatura subindo gradualmente ao longo
    # de horas pode indicar falha no sistema de resfriamento.
    #
    gr.Markdown("### 📈 Histórico das Últimas 24h")
    gr.Markdown(
        "_Intervalo de 30 min entre amostras (48 pontos). "
        "Linhas tracejadas: limites de Aviso (laranja) e Crítico (vermelho)._"
    )

    grafico = gr.Plot(label="")

    gr.Markdown("---")

    # ── Seção 4: Placa de Identificação Simulada ─────────────────────────────
    #
    # Em produção (Sprint 3), esta seção exibirá a foto real da placa do motor,
    # lida automaticamente via Visão Computacional.
    # Por ora, os dados são os mesmos do cadastro técnico.
    #
    gr.Markdown("### 🏷️ Placa de Identificação")

    placa = gr.Markdown(
        value="_Selecione um equipamento para exibir a placa._"
    )

    # ── Eventos ─────────────────────────────────────────────────────────────

    # Quando a Planta muda → recarrega as Áreas (e limpa o dropdown de TAGs)
    def _ao_selecionar_planta(planta):
        areas = planta_provider.listar_areas(planta)
        # value=None limpa a seleção atual dos dropdowns dependentes
        return gr.update(choices=areas, value=None), gr.update(choices=[], value=None)

    dd_planta.change(
        fn=_ao_selecionar_planta,
        inputs=dd_planta,
        outputs=[dd_area, dd_equip],
    )

    # Quando a Área muda → recarrega os Equipamentos daquela área
    def _ao_selecionar_area(planta, area):
        equips = planta_provider.listar_equipamentos(planta, area)
        return gr.update(choices=equips, value=None)

    dd_area.change(
        fn=_ao_selecionar_area,
        inputs=[dd_planta, dd_area],
        outputs=dd_equip,
    )

    # Quando o Equipamento muda → carrega todos os dados do dashboard
    def _carregar_dashboard(tag: str):
        if not tag:
            return (
                "_Selecione um equipamento._",
                None,
                "_Selecione um equipamento._",
            )
        return (
            pipeline.cards_telemetria_md(tag),
            pipeline.grafico_historico(tag),
            pipeline.placa_md(tag),
        )

    dd_equip.change(
        fn=_carregar_dashboard,
        inputs=dd_equip,
        outputs=[cards_md, grafico, placa],
    )

    # Botão Atualizar → gera nova leitura instantânea (simula polling de sensor)
    botao_atualizar.click(
        fn=_carregar_dashboard,
        inputs=dd_equip,
        outputs=[cards_md, grafico, placa],
    )

    # ── Integração com navegação externa ─────────────────────────────────────
    #
    # Quando o usuário chega ao dashboard pela lista de Equipamentos
    # (ex: futuro botão "Ver Dashboard"), a TAG já está em state.tag_selecionada.
    # Aqui pré-preenchemos os três dropdowns e carregamos o dashboard completo.
    #
    def _carregar_por_tag_externa(tag: str):
        if not tag:
            return (
                gr.update(),              # planta — sem mudança
                gr.update(),              # area   — sem mudança
                gr.update(),              # equip  — sem mudança
                "_Selecione um equipamento._",
                None,
                "_Selecione um equipamento._",
            )

        # Descobre em qual planta/área o equipamento está instalado
        planta, area = planta_provider.buscar_localizacao(tag)
        areas  = planta_provider.listar_areas(planta)
        equips = planta_provider.listar_equipamentos(planta, area)

        return (
            gr.update(value=planta),
            gr.update(choices=areas,  value=area),
            gr.update(choices=equips, value=tag),
            pipeline.cards_telemetria_md(tag),
            pipeline.grafico_historico(tag),
            pipeline.placa_md(tag),
        )

    # Escuta mudanças na tag compartilhada — dispara quando outra página
    # define uma TAG e navega para o dashboard
    state.tag_selecionada.change(
        fn=_carregar_por_tag_externa,
        inputs=state.tag_selecionada,
        outputs=[dd_planta, dd_area, dd_equip, cards_md, grafico, placa],
    )
