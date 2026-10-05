# =============================================================================
# pipelines/dashboard_pipeline.py — Painel de um motor, pronto para a tela
#
# Ordem de leitura pensada para o celular, "o status primeiro":
#   1. resumo   — o motor está bem? Uma frase responde em dois segundos.
#   2. grandezas — os cinco valores, com tendência em miniatura.
#   3. gráfico   — UMA grandeza por vez, em detalhe.
#   4. placa     — dados de cadastro, sob demanda.
# =============================================================================

import plotly.graph_objects as go

import providers.api_provider as api_provider
from pipelines.formatacao import GRANDEZAS, LIMITES, com_unidade, hora, numero
from pipelines.sensor_pipeline import grandezas_atuais
from ui.tokens import cores, pior_severidade


def _explicar(leitura: dict) -> str:
    """
    Frase que justifica o status-resumo.

    É o pilar de transparência aplicado ao celular: em vez de só uma cor,
    a tela diz QUAL grandeza disparou o alarme e QUAL limite foi ultrapassado.
    """
    frases = []
    for chave in ("temp_c", "vibracao_mms"):
        sev = leitura[GRANDEZAS[chave]["chave_sev"]]
        if sev in ("aviso", "critico"):
            limite = LIMITES[chave][sev]
            nivel = "crítico" if sev == "critico" else "de aviso"
            frases.append(
                f"{GRANDEZAS[chave]['nome']} em {com_unidade(chave, leitura[chave])}, "
                f"acima do limite {nivel} de {numero(limite, GRANDEZAS[chave]['casas'])} "
                f"{GRANDEZAS[chave]['unidade']}."
            )
    return " ".join(frases) or "Todas as grandezas dentro dos limites."


def painel(tag: str) -> dict | None:
    """Resumo + grandezas de um motor. None quando o motor não existe ou a API falhou."""
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return None
    leitura = api_provider.leitura_atual(tag)
    grandezas = grandezas_atuais(tag)
    if not grandezas:
        return None

    sev_geral = pior_severidade(leitura["severidade_temp"], leitura["severidade_vibracao"])
    # A grandeza mais grave abre selecionada no gráfico de detalhe.
    destaque = max(("temp_c", "vibracao_mms"),
                   key=lambda c: {"critico": 2, "aviso": 1}.get(leitura[GRANDEZAS[c]["chave_sev"]], 0))

    return {
        "tag": eq["tag"],
        "titulo": f"{eq['modelo']} · {eq['fabricante']}",
        "local": eq["local"],
        "status_operacional": eq["status"],
        "severidade": sev_geral,
        "explicacao": _explicar(leitura),
        "hora": hora(leitura["timestamp"]),
        "grandezas": grandezas["itens"],
        "grandeza_destaque": destaque,
    }


def grafico_grandeza(tag: str, chave: str, modo_tema: str = "claro"):
    """
    Gráfico de UMA grandeza nas últimas 24 h, desenhado para o toque.

    Três decisões de mobile:
      - altura de 260 px: cabe na tela junto com o título;
      - eixos travados (fixedrange) e sem arrastar: o dedo rola a PÁGINA,
        não o gráfico — evita a "armadilha de rolagem";
      - linhas de limite nas cores semânticas do design system.
    """
    historico = api_provider.historico_simulado(tag)
    if not historico:
        return None

    t = cores(modo_tema)
    g = GRANDEZAS[chave]
    x = [h["timestamp"] for h in historico]
    y = [h[chave] for h in historico]

    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="lines", line=dict(color=t["acao"], width=2.5),
        hovertemplate=f"%{{x|%H:%M}} · %{{y:.{g['casas']}f}} {g['unidade']}<extra></extra>",
    ))
    for nivel, cor in (("aviso", t["aviso_destaque"]), ("critico", t["critico_destaque"])):
        if chave in LIMITES:
            fig.add_hline(y=LIMITES[chave][nivel], line_dash="dash", line_color=cor, line_width=1.5,
                          annotation_text="Crítico" if nivel == "critico" else "Aviso",
                          annotation_position="top left", annotation_font_color=cor)

    fig.update_layout(
        template="plotly_white",   # fundo neutro: a cor fica para os limites e a série
        height=260, margin=dict(t=16, b=8, l=8, r=8), showlegend=False,
        dragmode=False, hovermode="x unified",
        yaxis_title=g["unidade"],
        # Quem exibe o gráfico pode não permitir esconder a barra de ferramentas
        # (o gr.Plot não permite); então os botões dela são removidos aqui.
        modebar_remove=["zoom", "pan", "select", "lasso2d", "zoomIn", "zoomOut",
                        "autoScale", "resetScale", "toImage"],
    )
    fig.update_xaxes(fixedrange=True, tickformat="%H:%M", nticks=5)
    fig.update_yaxes(fixedrange=True)
    return fig


def placa(tag: str) -> list[tuple[str, str]]:
    """Placa de identificação como pares rótulo/valor (antes: arte ASCII de 48 colunas)."""
    eq = api_provider.buscar_por_tag(tag)
    if not eq:
        return []
    return [
        ("Potência", f"{numero(eq['potencia_cv'], 1)} cv"),
        ("Tensão", f"{eq['tensao_v']} V"),
        ("Corrente nominal", f"{numero(eq['corrente_nominal_a'], 1)} A"),
        ("Fator de potência", numero(eq["fator_potencia"], 2)),
        ("Rotação", f"{numero(eq['rotacao_rpm'], 0)} RPM"),
        ("Isolamento", f"Classe {eq['classe_isolamento']}"),
        ("Proteção", eq["ip"]),
        ("Peso", f"{numero(eq['peso_kg'], 1)} kg"),
    ]
