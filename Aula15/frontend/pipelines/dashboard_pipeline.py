# =============================================================================
# pipelines/dashboard_pipeline.py — Lógica de apresentação do Dashboard
#
# Responsabilidades (100% apresentação — por isso continua no front-end):
#   1. Montar cards de telemetria em tempo real com cores semânticas
#   2. Gerar gráficos de série temporal com Plotly (histórico 24h)
#   3. Formatar a placa técnica simulada do equipamento
#
# A classificação de severidade em si (o que é normal/aviso/crítico) vem
# pronta do back-end — este arquivo só decide como desenhar.
# =============================================================================

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import providers.api_provider as api_provider

_ICONE_SEV = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}


def _icone_status(status: str) -> str:
    """Retorna o ícone semântico de acordo com o status operacional."""
    return {"Operacional": "🟢", "Em Manutenção": "🟡", "Desligado": "⚫"}.get(status, "⚪")


def cards_telemetria_md(tag: str) -> str:
    """
    Retorna Markdown com a leitura atual do equipamento e alertas semânticos.
    """
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return f"_Equipamento **{tag}** não encontrado no cadastro._"

    leitura = api_provider.leitura_atual(tag)

    cor_temp = _ICONE_SEV[leitura["severidade_temp"]]
    cor_vibr = _ICONE_SEV[leitura["severidade_vibracao"]]

    md  = f"### {_icone_status(eq['status'])} **{tag}** — {eq['modelo']} | Status: _{eq['status']}_\n"
    md += f"`Leitura em: {leitura['timestamp']}`\n\n"
    md += "| Grandeza | Valor | Unidade | Alerta |\n"
    md += "|---|---|---|:---:|\n"
    md += f"| Temperatura de Carcaça | **{leitura['temp_c']}** | °C | {cor_temp} |\n"
    md += f"| Vibração RMS (ISO 10816) | **{leitura['vibracao_mms']}** | mm/s | {cor_vibr} |\n"
    md += f"| Corrente de Fase | **{leitura['corrente_a']}** | A | 🟢 |\n"
    md += f"| Tensão Linha-Linha | **{leitura['tensao_v']}** | V | 🟢 |\n"
    md += f"| Rotação Real | **{leitura['rotacao_rpm']}** | RPM | 🟢 |\n"
    md += "\n_🟢 Normal · 🟡 Aviso · 🔴 Crítico — classificação calculada pelo back-end_"

    return md


def grafico_historico(tag: str):
    """
    Gera uma figura Plotly com 4 subplots mostrando as últimas 24h do motor.

    Nota de aula: os valores 75/90 e 4.5/7.1 usados para desenhar as linhas
    de referência são os MESMOS limites que o back-end usa para calcular
    severidade_temp/severidade_vibracao (backend/routers/sensores.py). Hoje
    eles estão duplicados aqui como constantes de desenho porque o gráfico
    só precisa da posição das linhas, não da classificação em si.
    Exercício proposto: criar GET /v1/sensores/limites no back-end e buscar
    esses valores em vez de hardcodar, eliminando a duplicação.
    """
    historico = api_provider.historico_simulado(tag)

    timestamps = [h["timestamp"]    for h in historico]
    temp       = [h["temp_c"]       for h in historico]
    vibracao   = [h["vibracao_mms"] for h in historico]
    corrente   = [h["corrente_a"]   for h in historico]
    rpm        = [h["rotacao_rpm"]  for h in historico]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "🌡️ Temperatura (°C)",
            "📳 Vibração (mm/s)",
            "⚡ Corrente (A)",
            "🔄 Rotação (RPM)",
        ),
        shared_xaxes=False,
        vertical_spacing=0.18,
        horizontal_spacing=0.10,
    )

    # — Temperatura —
    fig.add_trace(
        go.Scatter(x=timestamps, y=temp, name="Temp °C",
                   line=dict(color="#e74c3c", width=2), fill="tozeroy",
                   fillcolor="rgba(231,76,60,0.08)"),
        row=1, col=1,
    )
    fig.add_hline(y=75, line_dash="dash", line_color="orange",
                  annotation_text="Aviso 75°C", annotation_position="top right",
                  row=1, col=1)
    fig.add_hline(y=90, line_dash="dash", line_color="red",
                  annotation_text="Crítico 90°C", annotation_position="top right",
                  row=1, col=1)

    # — Vibração —
    fig.add_trace(
        go.Scatter(x=timestamps, y=vibracao, name="Vibração mm/s",
                   line=dict(color="#9b59b6", width=2), fill="tozeroy",
                   fillcolor="rgba(155,89,182,0.08)"),
        row=1, col=2,
    )
    fig.add_hline(y=4.5, line_dash="dash", line_color="orange",
                  annotation_text="Aviso 4.5", annotation_position="top right",
                  row=1, col=2)
    fig.add_hline(y=7.1, line_dash="dash", line_color="red",
                  annotation_text="Crítico 7.1", annotation_position="top right",
                  row=1, col=2)

    # — Corrente —
    fig.add_trace(
        go.Scatter(x=timestamps, y=corrente, name="Corrente A",
                   line=dict(color="#3498db", width=2), fill="tozeroy",
                   fillcolor="rgba(52,152,219,0.08)"),
        row=2, col=1,
    )

    # — Rotação —
    fig.add_trace(
        go.Scatter(x=timestamps, y=rpm, name="RPM",
                   line=dict(color="#27ae60", width=2), fill="tozeroy",
                   fillcolor="rgba(39,174,96,0.08)"),
        row=2, col=2,
    )

    fig.update_layout(
        title=dict(text=f"📈 Histórico 24h — {tag}", font=dict(size=16)),
        height=480,
        showlegend=False,
        margin=dict(t=80, b=40, l=50, r=40),
        paper_bgcolor="white",
        plot_bgcolor="#f9f9f9",
    )

    fig.update_xaxes(tickangle=-30, tickfont=dict(size=9))

    return fig


def placa_md(tag: str) -> str:
    """
    Retorna Markdown simulando a placa de identificação do motor.
    """
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return "_Nenhum equipamento selecionado._"

    return f"""
> 📷 **Simulação** — em produção, esta seção exibirá a foto real da placa
> extraída via Visão Computacional (Sprint 3).

```
╔══════════════════════════════════════════════╗
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
╚══════════════════════════════════════════════╝
```
"""
