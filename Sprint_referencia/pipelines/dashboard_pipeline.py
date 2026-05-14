# =============================================================================
# pipelines/dashboard_pipeline.py — Lógica de negócio do Dashboard (Sprint 2)
#
# Responsabilidades:
#   1. Montar cards de telemetria em tempo real com cores semânticas
#   2. Gerar gráficos de série temporal com Plotly (histórico 24h)
#   3. Formatar a placa técnica simulada do equipamento
#
# Por que Plotly?
# ---------------
# O Gradio suporta gr.Plot nativamente com Plotly. É a biblioteca de gráficos
# mais usada no ecossistema Python para dashboards industriais e de dados.
# Subplots permitem mostrar múltiplas grandezas em um único componente visual.
# =============================================================================

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import providers.sensor_provider   as sensor_provider
import providers.equipamento_provider as eq_provider


# ---------------------------------------------------------------------------
# _LIMITES — mesmos thresholds do sensor_pipeline para consistência visual
#
# Esses limites são usados tanto para colorir os cards de status quanto
# para desenhar as linhas de alerta nos gráficos temporais.
# ---------------------------------------------------------------------------
_LIMITES = {
    "temp_c":       {"aviso": 75,  "critico": 90},
    "vibracao_mms": {"aviso": 4.5, "critico": 7.1},
}


def _icone_status(status: str) -> str:
    """Retorna o ícone semântico de acordo com o status operacional."""
    return {"Operacional": "🟢", "Em Manutenção": "🟡", "Desligado": "⚫"}.get(status, "⚪")


def _severidade(chave: str, valor: float) -> str:
    """
    Classifica a severidade de uma leitura: 'normal', 'aviso' ou 'critico'.
    Grandezas sem limite definido retornam sempre 'normal'.
    """
    limites = _LIMITES.get(chave)
    if not limites:
        return "normal"
    if valor >= limites["critico"]:
        return "critico"
    if valor >= limites["aviso"]:
        return "aviso"
    return "normal"


def cards_telemetria_md(tag: str) -> str:
    """
    Retorna Markdown com a leitura atual do equipamento e alertas semânticos.

    Cada grandeza tem um ícone de severidade (🟢/🟡/🔴) para que o operador
    identifique o estado de saúde do ativo de forma imediata.

    Retorna string Markdown pronta para gr.Markdown.
    """
    eq = eq_provider.buscar_por_tag(tag)
    if not eq:
        return f"_Equipamento **{tag}** não encontrado no cadastro._"

    status  = eq["status"]
    leitura = sensor_provider.leitura_atual(tag, status)

    icone_sev = {"normal": "🟢", "aviso": "🟡", "critico": "🔴"}

    cor_temp = icone_sev[_severidade("temp_c",       leitura["temp_c"])]
    cor_vibr = icone_sev[_severidade("vibracao_mms", leitura["vibracao_mms"])]

    md  = f"### {_icone_status(status)} **{tag}** — {eq['modelo']} | Status: _{status}_\n"
    md += f"`Leitura em: {leitura['timestamp']}`\n\n"
    md += "| Grandeza | Valor | Unidade | Alerta |\n"
    md += "|---|---|---|:---:|\n"
    md += f"| Temperatura de Carcaça | **{leitura['temp_c']}** | °C | {cor_temp} |\n"
    md += f"| Vibração RMS (ISO 10816) | **{leitura['vibracao_mms']}** | mm/s | {cor_vibr} |\n"
    md += f"| Corrente de Fase | **{leitura['corrente_a']}** | A | 🟢 |\n"
    md += f"| Tensão Linha-Linha | **{leitura['tensao_v']}** | V | 🟢 |\n"
    md += f"| Rotação Real | **{leitura['rotacao_rpm']}** | RPM | 🟢 |\n"
    md += "\n_🟢 Normal · 🟡 Aviso · 🔴 Crítico — limites ISO 10816 e dados cadastrais_"

    return md


def grafico_historico(tag: str):
    """
    Gera uma figura Plotly com 4 subplots mostrando as últimas 24h do motor.

    Grandezas exibidas:
      - Temperatura (°C)     — com linhas de alerta
      - Vibração (mm/s)      — com linhas de alerta
      - Corrente (A)
      - Rotação (RPM)

    As linhas tracejadas indicam os limites de Aviso (laranja) e Crítico (vermelho).
    Retorna uma figura Plotly pronta para o componente gr.Plot do Gradio.
    """
    eq     = eq_provider.buscar_por_tag(tag)
    status = eq["status"] if eq else "Operacional"

    historico = sensor_provider.historico_simulado(tag, status)

    # Extrai cada série temporal do histórico
    timestamps = [h["timestamp"]    for h in historico]
    temp       = [h["temp_c"]       for h in historico]
    vibracao   = [h["vibracao_mms"] for h in historico]
    corrente   = [h["corrente_a"]   for h in historico]
    rpm        = [h["rotacao_rpm"]  for h in historico]

    # Cria a figura com 2 linhas × 2 colunas de subplots
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
    # Linha de aviso e linha crítica como linhas horizontais pontilhadas
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

    # Eixos X sem rótulos repetidos (são timestamps, o Plotly já gerencia)
    fig.update_xaxes(tickangle=-30, tickfont=dict(size=9))

    return fig


def placa_md(tag: str) -> str:
    """
    Retorna Markdown simulando a placa de identificação do motor.

    Na Sprint 2, a placa é simulada com os dados do cadastro técnico.
    Em produção (Sprint 3): substituir pela imagem real lida via Visão Computacional.
    """
    eq = eq_provider.buscar_por_tag(tag)
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
