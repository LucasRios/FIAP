# =============================================================================
# AULA: GRÁFICOS NO GRADIO — DO BÁSICO AO AVANÇADO
# Duração estimada: 2 horas
# Estrutura:
#   BLOCO 1 — Componentes Nativos do Gradio (gr.LinePlot, gr.BarPlot, gr.ScatterPlot)
#   BLOCO 2 — gr.Plot com Matplotlib (gráficos customizados)
#   BLOCO 3 — gr.Plot com Plotly (interatividade avançada)
#   BLOCO 4 — Matplotlib com imagem de fundo no plano cartesiano
#   BLOCO 5 — gr.Image com PIL: desenhar bolas sobre uma imagem
# =============================================================================

# --- INSTALAÇÃO (rode no terminal antes de abrir o Python) ---
# pip install gradio pandas numpy matplotlib plotly pillow

import gradio as gr
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageDraw
import io
import urllib.request

matplotlib.use("Agg")  # Força backend sem janela, necessário para servidores


# =============================================================================
# ███████████████████████████████████████████████████████████
# BLOCO 1 — COMPONENTES NATIVOS DO GRADIO
# gr.LinePlot | gr.ScatterPlot | gr.BarPlot
#
# CONCEITO CHAVE:
#   - Recebem um pandas DataFrame como valor
#   - Você aponta as colunas com x= e y=
#   - Não precisam de função Python — renderizam direto
#   - Todos têm a mesma API (troca o nome, o resto é igual)
# ███████████████████████████████████████████████████████████
# =============================================================================

# --- Dados de exemplo: sensores de temperatura (contexto Forzy/IoT) ---
dados_sensores = pd.DataFrame({
    "hora":        [0, 1, 2, 3, 4, 5, 6, 7, 8],
    "temperatura": [42, 45, 43, 50, 55, 52, 48, 47, 49],
    "vibração":    [0.1, 0.2, 0.15, 0.4, 0.5, 0.45, 0.3, 0.25, 0.28],
    "motor":       ["M1", "M1", "M1", "M2", "M2", "M2", "M3", "M3", "M3"],
})


# ── 1A. LinePlot: série temporal simples ─────────────────────────────────────
# gr.LinePlot conecta os pontos em ordem — ideal para dados temporais
bloco_1a = gr.LinePlot(
    value=dados_sensores,       # DataFrame com os dados
    x="hora",                   # Coluna do eixo X
    y="temperatura",            # Coluna do eixo Y (deve ser numérica)
    title="Temperatura ao longo do tempo",
    x_title="Hora do turno",
    y_title="Temperatura (°C)",
    tooltip=["hora", "temperatura"],  # Aparece ao passar o mouse
)


# ── 1B. LinePlot com séries por cor ──────────────────────────────────────────
# color= divide os dados em séries, uma linha por categoria
bloco_1b = gr.LinePlot(
    value=dados_sensores,
    x="hora",
    y="temperatura",
    color="motor",              # Cada valor único de 'motor' vira uma cor/série
    title="Temperatura por Motor",
    tooltip=["hora", "temperatura", "motor"],
)


# ── 1C. ScatterPlot: pontos sem conexão ──────────────────────────────────────
# Útil para ver correlação entre duas variáveis
bloco_1c = gr.ScatterPlot(
    value=dados_sensores,
    x="temperatura",
    y="vibração",
    color="motor",
    title="Correlação: Temperatura × Vibração",
    tooltip=["temperatura", "vibração", "motor"],
)


# ── 1D. BarPlot com agregação ────────────────────────────────────────────────
# y_aggregate="mean" calcula a média de Y para cada valor único de X
bloco_1d = gr.BarPlot(
    value=dados_sensores,
    x="motor",                  # Eixo X categórico → vira barras automaticamente
    y="temperatura",
    y_aggregate="mean",         # Opções: "sum", "mean", "min", "max", "count"
    title="Temperatura Média por Motor",
    x_title="Motor",
    y_title="Média (°C)",
)


# ── 1E. LinePlot INTERATIVO: filtrado por dropdown ───────────────────────────
# Aqui entra um gr.Dropdown que filtra o DataFrame antes de plotar
def filtrar_por_motor(motor_selecionado):
    """Filtra o DataFrame e retorna um novo LinePlot com os dados filtrados."""
    if motor_selecionado == "Todos":
        dados_filtrados = dados_sensores
    else:
        # Seleciona apenas as linhas onde a coluna 'motor' tem o valor escolhido
        dados_filtrados = dados_sensores[dados_sensores["motor"] == motor_selecionado]

    # Retorna um novo componente LinePlot com os dados filtrados
    return gr.LinePlot(value=dados_filtrados, x="hora", y="temperatura")


# =============================================================================
# ███████████████████████████████████████████████████████████
# BLOCO 2 — gr.Plot COM MATPLOTLIB
#
# CONCEITO CHAVE:
#   - gr.Plot() é um container genérico para figuras externas
#   - Aceita: matplotlib.Figure, plotly.Figure, bokeh, altair
#   - A função Python cria a figura e a retorna — Gradio exibe
#   - Dá controle total sobre o visual (cores, fontes, layouts)
# ███████████████████████████████████████████████████████████
# =============================================================================

def grafico_matplotlib_basico():
    """
    Cria e retorna uma figura Matplotlib.
    Gradio exibe a figura no gr.Plot() de saída.
    """
    # Gera dados: sinal senoidal simulando vibração de motor
    tempo = np.linspace(0, 4 * np.pi, 300)   # 300 pontos de 0 a 4π
    sinal = np.sin(tempo) * np.exp(-tempo / 10)  # Senoide com amortecimento

    # Cria a figura e o eixo explicitamente (boa prática)
    figura, eixo = plt.subplots(figsize=(8, 4))

    # Plota a linha com estilo customizado
    eixo.plot(tempo, sinal, color="#E84393", linewidth=2, label="Sinal de vibração")

    # Linha horizontal em y=0 para referência
    eixo.axhline(0, color="gray", linewidth=0.8, linestyle="--")

    # Configura rótulos e título
    eixo.set_title("Sinal de Vibração Amortecida", fontsize=14)
    eixo.set_xlabel("Tempo (rad)")
    eixo.set_ylabel("Amplitude")
    eixo.legend()

    # Ajusta margens para não cortar rótulos
    figura.tight_layout()

    return figura   # Gradio captura essa figura e exibe no gr.Plot()


def grafico_matplotlib_com_parametros(frequencia, amplitude):
    """
    Cria um gráfico Matplotlib controlado por sliders do Gradio.
    frequencia: float — frequência da onda
    amplitude:  float — amplitude máxima
    """
    tempo = np.linspace(0, 2 * np.pi, 400)

    # Calcula sinal com os parâmetros fornecidos pelo usuário
    sinal = amplitude * np.sin(frequencia * tempo)

    figura, eixo = plt.subplots(figsize=(8, 4))
    eixo.plot(tempo, sinal, color="#0073e6", linewidth=2)
    eixo.set_ylim(-10, 10)       # Eixo Y fixo para o slider não "pular"
    eixo.set_title(f"Onda: frequência={frequencia:.1f}, amplitude={amplitude:.1f}")
    eixo.set_xlabel("Tempo (rad)")
    eixo.set_ylabel("Amplitude")
    figura.tight_layout()

    return figura


# =============================================================================
# ███████████████████████████████████████████████████████████
# BLOCO 3 — gr.Plot COM PLOTLY
#
# CONCEITO CHAVE:
#   - Plotly gera gráficos interativos (zoom, hover, pan nativo)
#   - plotly.express (px) → API de alto nível, uma linha por gráfico
#   - plotly.graph_objects (go) → controle total, componente a componente
#   - gr.Plot() recebe um plotly.Figure diretamente
# ███████████████████████████████████████████████████████████
# =============================================================================

def grafico_plotly_express():
    """
    Usa plotly.express — ideal para gráficos rápidos a partir de DataFrames.
    """
    # Cria DataFrame com histórico de temperatura de 3 motores
    df = pd.DataFrame({
        "hora":        list(range(24)) * 3,
        "temperatura": (
            [40 + np.random.randint(-3, 3) for _ in range(24)] +  # Motor A
            [50 + np.random.randint(-3, 3) for _ in range(24)] +  # Motor B
            [35 + np.random.randint(-3, 3) for _ in range(24)]    # Motor C
        ),
        "motor": ["Motor A"] * 24 + ["Motor B"] * 24 + ["Motor C"] * 24,
    })

    # px.line cria automaticamente uma linha por categoria em color=
    figura = px.line(
        df,
        x="hora",
        y="temperatura",
        color="motor",
        title="Temperatura ao longo do dia — 3 Motores",
        labels={"hora": "Hora do dia", "temperatura": "Temperatura (°C)"},
        template="plotly_white",  # Tema visual limpo
    )

    return figura


def grafico_plotly_gauge(valor_temperatura):
    """
    Cria um gauge (velocímetro) com plotly.graph_objects.
    Útil para dashboards de monitoramento — leitura instantânea do sensor.
    valor_temperatura: float — leitura atual do sensor
    """
    # Define zonas de cor: verde (ok), amarelo (atenção), vermelho (alarme)
    figura = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=valor_temperatura,
        delta={"reference": 45},    # Valor de referência para o delta (seta)
        title={"text": "Temperatura do Motor (°C)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#0073e6"},
            "steps": [
                {"range": [0, 40],   "color": "#d4edda"},   # Verde: normal
                {"range": [40, 70],  "color": "#fff3cd"},   # Amarelo: atenção
                {"range": [70, 100], "color": "#f8d7da"},   # Vermelho: alarme
            ],
            "threshold": {
                "line": {"color": "red", "width": 3},
                "thickness": 0.75,
                "value": 70,       # Linha vermelha de limite crítico
            },
        },
    ))

    figura.update_layout(height=350)
    return figura


def grafico_plotly_3d():
    """
    Gráfico de superfície 3D — mostra temperatura em função de X e Y (posição).
    Simula um mapa de calor espacial de um motor.
    """
    # Cria grade 20x20 de pontos
    x_valores = np.linspace(-3, 3, 20)
    y_valores = np.linspace(-3, 3, 20)
    X, Y = np.meshgrid(x_valores, y_valores)

    # Superfície: simula distribuição de temperatura no motor
    Z = np.sin(np.sqrt(X**2 + Y**2)) * 30 + 50   # Valores entre ~20°C e ~80°C

    figura = go.Figure(go.Surface(
        z=Z,
        x=X,
        y=Y,
        colorscale="RdYlGn_r",    # Verde = frio, Vermelho = quente
        colorbar={"title": "°C"},
    ))

    figura.update_layout(
        title="Mapa de Calor 3D do Motor",
        scene={
            "xaxis_title": "Posição X",
            "yaxis_title": "Posição Y",
            "zaxis_title": "Temperatura (°C)",
        },
        height=500,
    )

    return figura


# =============================================================================
# ███████████████████████████████████████████████████████████
# BLOCO 4 — MATPLOTLIB: IMAGEM DE FUNDO NO PLANO CARTESIANO
#
# CONCEITO CHAVE:
#   - ax.imshow() renderiza uma imagem como fundo do eixo
#   - extent=[xmin, xmax, ymin, ymax] define as coordenadas cartesianas
#     que a imagem ocupa — isso alinha a imagem com os eixos numéricos
#   - Depois você plota normalmente sobre o eixo (scatter, plot, etc.)
#   - Útil para: plantas de fábrica, esquemas de motores, mapas
# ███████████████████████████████████████████████████████████
# =============================================================================

def baixar_imagem_planta():
    """
    Baixa uma imagem pública de exemplo para usar como fundo.
    Retorna um array numpy (formato que imshow aceita).
    Em produção você carregaria do disco: Image.open("planta.png")
    """
    url = "https://dummyimage.com/800x600/add8e6/add8e6.png"
    try:
        # Baixa os bytes da imagem e abre com PIL
        with urllib.request.urlopen(url, timeout=5) as resposta:
            bytes_imagem = resposta.read()
        imagem_pil = Image.open(io.BytesIO(bytes_imagem)).convert("RGB")
        return np.array(imagem_pil)   # Converte para array numpy (H, W, 3)
    except Exception:
        # Fallback: cria uma imagem colorida sintética se o download falhar
        imagem_sintetica = np.zeros((200, 300, 3), dtype=np.uint8)
        imagem_sintetica[:, :, 0] = 200   # Canal vermelho: fundo avermelhado
        return imagem_sintetica


# Carrega a imagem uma vez quando o módulo é importado
IMAGEM_FUNDO = baixar_imagem_planta()

def gerar_grafico_com_fundo():
    # 1. Cria a figura e adiciona alguns dados de exemplo
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[1, 2, 3, 4, 5], 
        y=[10, 15, 13, 17, 20], 
        mode="lines+markers",
        line=dict(color="red", width=4),
        marker=dict(size=12)
    ))

    # 2. Adiciona a imagem de fundo
    fig.add_layout_image(
        dict(
            # Pode ser uma URL ou uma imagem em Base64 (para arquivos locais)
            source="https://dummyimage.com/800x600/add8e6/add8e6.png",
            
            # Usar 'paper' faz a imagem se basear no tamanho do gráfico, não nos eixos X/Y
            xref="paper", 
            yref="paper",
            
            # Posição inicial (topo esquerdo)
            x=0, 
            y=1,
            
            # Tamanho (1 = 100% da área do gráfico)
            sizex=1, 
            sizey=1,
            
            # 'stretch' estica a imagem, 'contain' mantém a proporção
            sizing="stretch",
            
            # Transparência da imagem
            opacity=0.3,
            
            # Fundamental: coloca a imagem ATRÁS das linhas do gráfico
            layer="below"
        )
    )

    # Opcional: remove o fundo cinza/branco padrão do Plotly para a imagem aparecer bem
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title="Gráfico com Imagem de Fundo",
    )

    return fig

def grafico_com_fundo(ponto_x, ponto_y):
    """
    Plota um gráfico com imagem de fundo no plano cartesiano.

    PASSO A PASSO:
      1. Definimos as coordenadas do plano cartesiano (0 a 10 em X, 0 a 10 em Y)
      2. Usamos imshow() para renderizar a imagem dentro dessas coordenadas
      3. Plotamos pontos normalmente — eles se sobrepõem à imagem

    ponto_x: float — coordenada X do ponto marcado pelo usuário
    ponto_y: float — coordenada Y do ponto marcado pelo usuário
    """
    # Define o espaço cartesiano: de 0 a 10 em ambos os eixos
    x_min, x_max = 0, 10
    y_min, y_max = 0, 10

    figura, eixo = plt.subplots(figsize=(7, 6))

    # ── CHAVE: imshow com extent ──────────────────────────────────────────────
    # extent=[esquerda, direita, baixo, cima] em unidades do EIXO CARTESIANO
    # aspect="auto" evita distorção — a imagem estica para preencher o extent
    # zorder=0 garante que a imagem fique ATRÁS dos outros elementos
    eixo.imshow(
        IMAGEM_FUNDO,
        extent=[x_min, x_max, y_min, y_max],
        aspect="auto",
        origin="upper",   # "upper" = linha 0 da imagem fica no TOPO do extent
        zorder=0,
        alpha=0.6,        # Transparência: 0=invisível, 1=opaco
    )

    # ── Plota ponto do usuário ────────────────────────────────────────────────
    # zorder=2 garante que o ponto fique ACIMA da imagem
    eixo.scatter(
        ponto_x, ponto_y,
        color="red",
        s=200,           # Tamanho do ponto em pontos²
        zorder=2,
        label=f"Sensor ({ponto_x:.1f}, {ponto_y:.1f})",
        edgecolors="white",
        linewidths=2,
    )

    # ── Plota alguns pontos fixos (simulando sensores existentes) ─────────────
    sensores_x = [2.0, 5.0, 8.0, 3.5]
    sensores_y = [3.0, 7.0, 2.0, 6.5]

    eixo.scatter(
        sensores_x, sensores_y,
        color="yellow",
        s=120,
        zorder=2,
        marker="^",      # Triângulo
        edgecolors="black",
        linewidths=1,
        label="Sensores fixos",
    )

    # ── Configurações do eixo ─────────────────────────────────────────────────
    eixo.set_xlim(x_min, x_max)
    eixo.set_ylim(y_min, y_max)
    eixo.set_xlabel("Posição X (metros)")
    eixo.set_ylabel("Posição Y (metros)")
    eixo.set_title("Planta da Fábrica — Posicionamento de Sensores")
    eixo.legend(loc="upper right")
    eixo.grid(True, alpha=0.3, zorder=1)   # Grade acima da imagem, abaixo dos pontos

    figura.tight_layout()
    return figura


# =============================================================================
# ███████████████████████████████████████████████████████████
# BLOCO 5 — gr.Image COM PIL: DESENHAR BOLAS SOBRE UMA IMAGEM
#
# CONCEITO CHAVE:
#   - gr.Image com type="pil" recebe e retorna objetos PIL.Image
#   - PIL.ImageDraw permite desenhar formas geométricas diretamente
#     nos pixels da imagem (coordenadas em pixels, não cartesianas)
#   - ellipse([(x0,y0),(x1,y1)]) desenha um círculo/elipse
#   - A imagem modificada é retornada ao gr.Image de saída
#   - DIFERENÇA do Bloco 4:
#       Bloco 4 = plano cartesiano com imagem de fundo (unidades métricas)
#       Bloco 5 = edição direta de pixels da imagem (unidades em pixels)
# ███████████████████████████████████████████████████████████
# =============================================================================

# Posições fixas de "alertas" para demonstração (em pixels relativos, 0.0 a 1.0)
# Usamos proporção (0 a 1) para que funcione em qualquer tamanho de imagem
POSICOES_ALERTAS = [
    {"cx": 0.25, "cy": 0.30, "raio": 0.04, "cor": (255, 0, 0, 180),   "label": "Alarme crítico"},
    {"cx": 0.60, "cy": 0.55, "raio": 0.03, "cor": (255, 200, 0, 180), "label": "Atenção"},
    {"cx": 0.80, "cy": 0.20, "raio": 0.03, "cor": (0, 200, 0, 180),   "label": "Normal"},
]


def desenhar_bolas_na_imagem(imagem_pil):
    """
    Recebe uma imagem PIL, desenha círculos coloridos sobre ela e retorna.

    PASSO A PASSO:
      1. Converte para RGBA para suportar transparência nas bolas
      2. Cria uma camada transparente separada para os círculos
      3. Desenha cada círculo na camada
      4. Combina a camada com a imagem original (Image.alpha_composite)
      5. Converte de volta para RGB e retorna

    imagem_pil: PIL.Image — imagem enviada pelo usuário no gr.Image
    """
    if imagem_pil is None:
        # Cria uma imagem cinza padrão se o usuário não enviou nada
        imagem_pil = Image.new("RGB", (640, 480), color=(180, 180, 180))

    # Garante que a imagem está em RGB antes de converter para RGBA
    imagem_rgb = imagem_pil.convert("RGB")

    # Converte para RGBA para permitir transparência (canal Alpha)
    imagem_rgba = imagem_rgb.convert("RGBA")
    largura, altura = imagem_rgba.size

    # ── Cria camada de overlay completamente transparente ─────────────────────
    # Vamos desenhar os círculos aqui, depois combinar com a imagem
    overlay = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    caneta = ImageDraw.Draw(overlay)

    # ── Desenha cada círculo (bola) no overlay ────────────────────────────────
    for alerta in POSICOES_ALERTAS:
        # Converte proporção (0-1) para pixels reais
        cx_pixels = int(alerta["cx"] * largura)
        cy_pixels = int(alerta["cy"] * altura)
        raio_pixels = int(alerta["raio"] * min(largura, altura))

        # ellipse() recebe [(x_esquerda, y_topo), (x_direita, y_base)]
        x0 = cx_pixels - raio_pixels
        y0 = cy_pixels - raio_pixels
        x1 = cx_pixels + raio_pixels
        y1 = cy_pixels + raio_pixels

        # Desenha o círculo preenchido
        caneta.ellipse(
            [(x0, y0), (x1, y1)],
            fill=alerta["cor"],        # Cor com canal alpha (R, G, B, A)
            outline=(255, 255, 255, 255),  # Borda branca sólida
            width=3,
        )

        # Escreve o label abaixo do círculo
        caneta.text(
            (cx_pixels - raio_pixels, y1 + 4),
            alerta["label"],
            fill=(255, 255, 255, 230),
        )

    # ── Combina overlay (círculos) com a imagem original ─────────────────────
    # alpha_composite "cola" o overlay sobre a imagem respeitando transparência
    imagem_final_rgba = Image.alpha_composite(imagem_rgba, overlay)

    # Converte de volta para RGB (gr.Image não precisa de canal Alpha na saída)
    imagem_final_rgb = imagem_final_rgba.convert("RGB")

    return imagem_final_rgb


def desenhar_bola_no_clique(imagem_pil, coordenadas_clique):
    """
    Versão interativa: o usuário clica em qualquer ponto da imagem
    e uma bola azul é desenhada onde clicou.

    coordenadas_clique: dict com {"x": int, "y": int} em pixels
                        (fornecido pelo evento .select do gr.Image)
    """
    if imagem_pil is None:
        imagem_pil = Image.new("RGB", (640, 480), color=(180, 180, 180))

    imagem_rgba = imagem_pil.convert("RGBA")
    overlay = Image.new("RGBA", imagem_rgba.size, (0, 0, 0, 0))
    caneta = ImageDraw.Draw(overlay)

    # Extrai coordenadas do clique
    cx = coordenadas_clique["x"]
    cy = coordenadas_clique["y"]
    raio = 20   # Raio fixo em pixels

    caneta.ellipse(
        [(cx - raio, cy - raio), (cx + raio, cy + raio)],
        fill=(0, 120, 255, 200),       # Azul semi-transparente
        outline=(255, 255, 255, 255),
        width=3,
    )

    resultado = Image.alpha_composite(imagem_rgba, overlay)
    return resultado.convert("RGB")


# =============================================================================
# ███████████████████████████████████████████████████████████
# MONTAGEM DA INTERFACE — gr.Blocks com Accordion por bloco
# ███████████████████████████████████████████████████████████
# =============================================================================

with gr.Blocks(title="Aula: Gráficos no Gradio") as demo:

    gr.Markdown("""# Gráficos no Gradio""")

    # ── Linha 1: Nativos ────────────────────────────────────────────────────────
    with gr.Accordion("1 — Nativos do Gradio"):
        gr.Markdown("""
        ### Componentes Nativos: `gr.LinePlot`, `gr.ScatterPlot`, `gr.BarPlot`
        - Recebem um **pandas DataFrame** diretamente
        - Basta apontar as colunas `x=` e `y=`
        - Todos têm a **mesma API** — troca o nome e o resto funciona igual
        - Interatividade embutida: zoom, pan, hover, seleção de região
        """)

        with gr.Row():
            # LinePlot simples
            gr.LinePlot(
                value=dados_sensores,
                x="hora",
                y="temperatura",
                title="1A — LinePlot: temperatura × hora",
                tooltip=["hora", "temperatura"],
            )

            # LinePlot com séries por cor
            gr.LinePlot(
                value=dados_sensores,
                x="hora",
                y="temperatura",
                color="motor",
                title="1B — LinePlot com séries por Motor",
                tooltip=["hora", "temperatura", "motor"],
            )

        with gr.Row():
            # ScatterPlot: correlação
            gr.ScatterPlot(
                value=dados_sensores,
                x="temperatura",
                y="vibração",
                color="motor",
                title="1C — ScatterPlot: Temperatura × Vibração",
                tooltip=["temperatura", "vibração", "motor"],
            )

            # BarPlot com agregação
            gr.BarPlot(
                value=dados_sensores,
                x="motor",
                y="temperatura",
                y_aggregate="mean",
                title="1D — BarPlot: Média de temperatura por Motor",
            )

        gr.Markdown("### 1E — LinePlot interativo: filtrado por Dropdown")
        gr.Markdown("Selecione um motor para filtrar os dados do gráfico:")

        with gr.Row():
            # Dropdown que controla o gráfico
            dropdown_motor = gr.Dropdown(
                choices=["Todos", "M1", "M2", "M3"],
                value="Todos",
                label="Filtrar por Motor",
            )

        grafico_filtrado = gr.LinePlot(
            value=dados_sensores,
            x="hora",
            y="temperatura",
            title="Temperatura — filtrada pelo dropdown",
        )

        # Quando o dropdown muda, chama filtrar_por_motor e atualiza o gráfico
        dropdown_motor.change(
            fn=filtrar_por_motor,
            inputs=dropdown_motor,
            outputs=grafico_filtrado,
        )

    # ── Linha 2: Matplotlib ────────────────────────────────────────────────────
    with gr.Accordion("2 — Matplotlib via gr.Plot"):
        gr.Markdown("""
        ### `gr.Plot` com Matplotlib
        - A função Python **cria** a figura e a **retorna**
        - Gradio exibe qualquer `matplotlib.Figure`
        - Você tem controle total: cores, fontes, subplots, anotações
        """)

        gr.Markdown("#### 2A — Gráfico fixo (carrega ao abrir)")
        grafico_matplotlib_fixo = gr.Plot(label="Sinal de Vibração Amortecida")

        # load() executa a função quando a página abre
        demo.load(fn=grafico_matplotlib_basico, outputs=grafico_matplotlib_fixo)

        gr.Markdown("#### 2B — Gráfico controlado por Sliders")

        with gr.Row():
            # Sliders que alimentam a função geradora do gráfico
            slider_frequencia = gr.Slider(
                minimum=0.5, maximum=5.0, value=1.0, step=0.1,
                label="Frequência da onda",
            )
            slider_amplitude = gr.Slider(
                minimum=1.0, maximum=8.0, value=3.0, step=0.5,
                label="Amplitude",
            )

        grafico_matplotlib_dinamico = gr.Plot(label="Onda controlada por sliders")

        # Qualquer mudança nos sliders regenera o gráfico
        slider_frequencia.change(
            fn=grafico_matplotlib_com_parametros,
            inputs=[slider_frequencia, slider_amplitude],
            outputs=grafico_matplotlib_dinamico,
        )
        slider_amplitude.change(
            fn=grafico_matplotlib_com_parametros,
            inputs=[slider_frequencia, slider_amplitude],
            outputs=grafico_matplotlib_dinamico,
        )
        # Carrega estado inicial
        demo.load(
            fn=grafico_matplotlib_com_parametros,
            inputs=[slider_frequencia, slider_amplitude],
            outputs=grafico_matplotlib_dinamico,
        )

    # ── Linha 3: Plotly ────────────────────────────────────────────────────────
    with gr.Accordion("3 — Plotly via gr.Plot"):
        gr.Markdown("""
        ### `gr.Plot` com Plotly
        - Plotly = gráficos **interativos nativos** (zoom, hover, download)
        - `plotly.express` → API simples, rápida, baseada em DataFrame
        - `plotly.graph_objects` → controle total de cada elemento
        - gr.Plot() aceita `plotly.Figure` diretamente
        """)

        gr.Markdown("#### 3A — plotly.express: múltiplas séries")
        grafico_px = gr.Plot(label="Temperatura — 3 Motores (Plotly Express)")
        demo.load(fn=grafico_plotly_express, outputs=grafico_px)

        gr.Markdown("#### 3B — Gauge (velocímetro) com graph_objects")

        with gr.Row():
            slider_gauge = gr.Slider(
                minimum=0, maximum=100, value=55, step=1,
                label="Temperatura atual do sensor (°C)",
            )

        grafico_gauge = gr.Plot(label="Gauge de Temperatura")

        slider_gauge.change(
            fn=grafico_plotly_gauge,
            inputs=slider_gauge,
            outputs=grafico_gauge,
        )
        demo.load(fn=lambda: grafico_plotly_gauge(55), outputs=grafico_gauge)

        gr.Markdown("#### 3C — Superfície 3D interativa")
        grafico_3d = gr.Plot(label="Mapa de Calor 3D do Motor")
        demo.load(fn=grafico_plotly_3d, outputs=grafico_3d)

    # ── Linha 4: Imagem de fundo no plano cartesiano ───────────────────────────
    with gr.Accordion("4 — Imagem de Fundo no Gráfico"):
        gr.Markdown("""
        ### Matplotlib: imagem de fundo no plano cartesiano
        - `ax.imshow(imagem, extent=[x0, x1, y0, y1])` posiciona a imagem
          dentro de coordenadas **cartesianas** (não pixels)
        - `extent` alinha a imagem com os eixos numéricos — essencial
        - `aspect="auto"` permite que a imagem distorça para preencher o espaço
        - Depois você plota pontos, linhas etc. normalmente **sobre** a imagem
        - Caso de uso: planta de fábrica com sensores mapeados por coordenadas métricas
        """)

        with gr.Row():
            slider_x = gr.Slider(minimum=0.0, maximum=10.0, value=4.0, step=0.5, label="X do novo sensor")
            slider_y = gr.Slider(minimum=0.0, maximum=10.0, value=4.0, step=0.5, label="Y do novo sensor")

        grafico_fundo = gr.Plot(label="Planta com sensores sobrepostos")

        slider_x.change(fn=grafico_com_fundo, inputs=[slider_x, slider_y], outputs=grafico_fundo)
        slider_y.change(fn=grafico_com_fundo, inputs=[slider_x, slider_y], outputs=grafico_fundo)
        demo.load(fn=lambda: grafico_com_fundo(4.0, 4.0), outputs=grafico_fundo)
        
        grafico_output = gr.Plot()
        
        demo.load(fn=gerar_grafico_com_fundo, inputs=[], outputs=grafico_output)



    # ── Linha 5: Bolas sobre imagem ─────────────────────────────────────────────
    with gr.Accordion("5 — Bolas sobre Imagem (PIL)"):
        gr.Markdown("""
        ### `gr.Image` + PIL: desenhar círculos diretamente nos pixels
        - `gr.Image(type="pil")` entrega e recebe objetos `PIL.Image`
        - `ImageDraw.Draw(imagem)` abre um "lápis" para desenhar
        - `caneta.ellipse([(x0,y0),(x1,y1)])` desenha círculo/elipse
        - Coordenadas em **pixels** — diferente do Bloco 4 (coordenadas métricas)
        - Técnica: cria camada transparente (RGBA), desenha nela, combina com a imagem
        """)

        gr.Markdown("#### 5A — Bolas fixas pré-definidas (alertas de sensor)")
        gr.Markdown("Envie qualquer imagem — os alertas serão desenhados em posições relativas (%):")

        with gr.Row():
            imagem_entrada_5a = gr.Image(
                type="pil",
                label="Imagem de entrada (upload ou câmera)",
            )
            imagem_saida_5a = gr.Image(
                label="Imagem com alertas desenhados",
            )

        botao_desenhar = gr.Button("Desenhar alertas na imagem", variant="primary")
        botao_desenhar.click(
            fn=desenhar_bolas_na_imagem,
            inputs=imagem_entrada_5a,
            outputs=imagem_saida_5a,
        )

        gr.Markdown("#### 5B — Clique para marcar ponto na imagem")
        gr.Markdown("""
        > **Como funciona:** `gr.Image` pode emitir evento `.select()` com as
        > coordenadas do pixel clicado. Usamos `gr.SelectData` para capturar
        > `(x, y)` e desenhar uma bola azul naquela posição.
        """)

        with gr.Row():
            imagem_clicavel = gr.Image(
                type="pil",
                label="Clique na imagem para marcar um ponto",
            )
            imagem_clicavel_saida = gr.Image(
                label="Imagem com ponto marcado",
            )

        # .select() captura o clique do usuário na imagem
        # gr.SelectData contém .index = (x_pixel, y_pixel)
        def marcar_ponto(imagem, dados_selecao: gr.SelectData):
            """
            Chamada quando o usuário clica na imagem de entrada.
            dados_selecao.index = (x_pixel, y_pixel) do clique
            """
            x_clique = dados_selecao.index[0]   # Pixel horizontal
            y_clique = dados_selecao.index[1]   # Pixel vertical

            coordenadas = {"x": x_clique, "y": y_clique}
            return desenhar_bola_no_clique(imagem, coordenadas)

        imagem_clicavel.select(
            fn=marcar_ponto,
            inputs=imagem_clicavel,
            outputs=imagem_clicavel_saida,
        )

    # ── Linha EXTRA: Resumo e referências ──────────────────────────────────────
    with gr.Accordion("📋 Resumo"):
        gr.Markdown("""
        ## Mapa mental da aula

        | Componente | Quando usar | Biblioteca |
        |---|---|---|
        | `gr.LinePlot` | Série temporal, tendência | Nativa Gradio |
        | `gr.ScatterPlot` | Correlação entre variáveis | Nativa Gradio |
        | `gr.BarPlot` | Comparação categórica | Nativa Gradio |
        | `gr.Plot` + Matplotlib | Gráfico customizado, estático, subplots | Matplotlib |
        | `gr.Plot` + Plotly | Interatividade rica, gauge, 3D, mapas | Plotly |
        | `gr.Plot` + imagem de fundo | Coordenadas reais sobrepostas à imagem | Matplotlib |
        | `gr.Image` + PIL | Edição de pixels, anotações visuais | PIL / Pillow |

        ## Referências
        - [Gradio — Creating Plots](https://www.gradio.app/guides/creating-plots)
        - [Gradio — Time Plots](https://www.gradio.app/guides/time-plots)
        - [Gradio — gr.Plot](https://www.gradio.app/docs/gradio/plot)
        - [Matplotlib imshow](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.imshow.html)
        - [Plotly Express](https://plotly.com/python/plotly-express/)
        - [PIL ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
        """)

demo.launch()