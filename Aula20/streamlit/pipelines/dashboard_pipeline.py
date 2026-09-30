# =============================================================================
# pipelines/dashboard_pipeline.py — Apresentação do Dashboard
#
# Responsabilidades (100% apresentação):
#   1. Preparar a telemetria para os cards do st.metric
#   2. Gerar o gráfico Plotly com o histórico das últimas 24h
#   3. Formatar a placa técnica simulada do equipamento
#
# O gráfico é idêntico ao da versão Gradio: o Plotly não sabe em qual
# biblioteca de UI vai ser desenhado. Só muda quem o exibe — era gr.Plot,
# agora é st.plotly_chart.
# =============================================================================

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import providers.api_provider as api_provider

ICONE_SEV = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}


def _icone_status(status: str) -> str:
    return {"Operacional": "🟢", "Em Manutenção": "🟡", "Desligado": "⚫"}.get(status, "⚪")


def telemetria(tag: str) -> dict | None:
    """
    Reúne cadastro e leitura atual num único dicionário pronto para a tela.

    Devolve None quando o equipamento não existe no cadastro.
    """
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return None

    leitura = api_provider.leitura_atual(tag)

    return {
        "titulo": f"{_icone_status(eq['status'])} {eq['tag']} — {eq['modelo']}",
        "status": eq["status"],
        "timestamp": leitura["timestamp"],
        "metricas": [
            ("Temperatura de Carcaça", f"{leitura['temp_c']} °C", ICONE_SEV[leitura["severidade_temp"]]),
            ("Vibração RMS (ISO 10816)", f"{leitura['vibracao_mms']} mm/s", ICONE_SEV[leitura["severidade_vibracao"]]),
            ("Corrente de Fase", f"{leitura['corrente_a']} A", "🟢"),
            ("Tensão Linha-Linha", f"{leitura['tensao_v']} V", "🟢"),
            ("Rotação Real", f"{leitura['rotacao_rpm']} RPM", "🟢"),
        ],
    }


def grafico_historico(tag: str):
    """
    Monta a figura Plotly com quatro subplots das últimas 24h.

    Nota de aula: os valores 75/90 e 4.5/7.1 são os MESMOS limites que o
    back-end usa para calcular a severidade. Aqui eles servem apenas para
    posicionar as linhas tracejadas. Exercício proposto: criar
    GET /v1/sensores/limites no back-end e buscar esses valores, eliminando
    a duplicação.
    """
    historico = api_provider.historico_simulado(tag)
    if not historico:
        return None

    timestamps = [h["timestamp"] for h in historico]
    temp = [h["temp_c"] for h in historico]
    vibracao = [h["vibracao_mms"] for h in historico]
    corrente = [h["corrente_a"] for h in historico]
    rpm = [h["rotacao_rpm"] for h in historico]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "🌡️ Temperatura (°C)",
            "📳 Vibração (mm/s)",
            "⚡ Corrente (A)",
            "🔄 Rotação (RPM)",
        ),
        vertical_spacing=0.18,
        horizontal_spacing=0.10,
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=temp, name="Temp °C",
                   line=dict(color="#e74c3c", width=2), fill="tozeroy",
                   fillcolor="rgba(231,76,60,0.08)"),
        row=1, col=1,
    )
    fig.add_hline(y=75, line_dash="dash", line_color="orange",
                  annotation_text="Aviso 75°C", annotation_position="top right", row=1, col=1)
    fig.add_hline(y=90, line_dash="dash", line_color="red",
                  annotation_text="Crítico 90°C", annotation_position="top right", row=1, col=1)

    fig.add_trace(
        go.Scatter(x=timestamps, y=vibracao, name="Vibração mm/s",
                   line=dict(color="#9b59b6", width=2), fill="tozeroy",
                   fillcolor="rgba(155,89,182,0.08)"),
        row=1, col=2,
    )
    fig.add_hline(y=4.5, line_dash="dash", line_color="orange",
                  annotation_text="Aviso 4.5", annotation_position="top right", row=1, col=2)
    fig.add_hline(y=7.1, line_dash="dash", line_color="red",
                  annotation_text="Crítico 7.1", annotation_position="top right", row=1, col=2)

    fig.add_trace(
        go.Scatter(x=timestamps, y=corrente, name="Corrente A",
                   line=dict(color="#3498db", width=2), fill="tozeroy",
                   fillcolor="rgba(52,152,219,0.08)"),
        row=2, col=1,
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=rpm, name="RPM",
                   line=dict(color="#27ae60", width=2), fill="tozeroy",
                   fillcolor="rgba(39,174,96,0.08)"),
        row=2, col=2,
    )

    fig.update_layout(
        title=dict(text=f"📈 Histórico 24h — {tag}", font=dict(size=16)),
        height=520,
        showlegend=False,
        margin=dict(t=80, b=40, l=50, r=40),
    )
    fig.update_xaxes(tickangle=-30, tickfont=dict(size=9))
    return fig


def placa_texto(tag: str) -> str | None:
    """Devolve a placa de identificação simulada como texto monoespaçado."""
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return None

    return f"""╔══════════════════════════════════════════════╗
║          PLACA DE IDENTIFICAÇÃO              ║
╠══════════════════════════════════════════════╣
║  TAG:            {eq['tag']}
║  Modelo:         {eq['modelo']}
║  Fabricante:     {eq['fabricante']}
╠══════════════════════════════════════════════╣
║  Potência:       {eq['potencia_cv']} cv
║  Tensão:         {eq['tensao_v']} V
║  Corrente Nom.:  {eq['corrente_nominal_a']} A
║  Fator de Pot.:  {eq['fator_potencia']}
║  Rotação:        {eq['rotacao_rpm']} RPM
╠══════════════════════════════════════════════╣
║  Isolamento:     Classe {eq['classe_isolamento']}
║  Proteção:       {eq['ip']}
║  Peso:           {eq['peso_kg']} kg
╚══════════════════════════════════════════════╝"""
