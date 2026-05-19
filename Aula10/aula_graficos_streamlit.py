# =============================================================================
# AULA: GRÁFICOS NO STREAMLIT — DO BÁSICO AO AVANÇADO
# Duração estimada: 2 horas
# Estrutura:
#   BLOCO 1 — Gráficos Nativos do Streamlit (st.line_chart, st.bar_chart, st.scatter_chart)
#   BLOCO 2 — st.pyplot com Matplotlib (gráficos customizados)
#   BLOCO 3 — st.plotly_chart com Plotly (interatividade avançada)
#   BLOCO 4 — Matplotlib com imagem de fundo no plano cartesiano
#   BLOCO 5 — st.image com PIL: desenhar bolas sobre uma imagem
# =============================================================================

# --- INSTALAÇÃO (rode no terminal antes de abrir o Python) ---
# pip install streamlit pandas numpy matplotlib plotly pillow

# --- COMO RODAR ---
# streamlit run aula_graficos_streamlit.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageDraw
import io
import urllib.request

matplotlib.use("Agg")  # Força backend sem janela, necessário para servidores

# =============================================================================
# DIFERENÇA FUNDAMENTAL ENTRE STREAMLIT E GRADIO
# -----------------------------------------------------------------------------
# No Gradio, você monta a interface como uma árvore de componentes com
# callbacks explícitos (.change(), .click()).
#
# No Streamlit, o script roda DE CIMA PRA BAIXO a cada interação do usuário.
# Quando o usuário move um slider, o Streamlit RE-EXECUTA todo o arquivo.
# Isso simplifica a lógica: você só escreve "o que mostrar", e o Streamlit
# cuida do "quando atualizar".
# =============================================================================

# --- Configuração da página (deve ser a primeira chamada Streamlit) ----------
st.set_page_config(
    page_title="Aula: Gráficos no Streamlit",
    layout="wide",      # Usa a largura toda da tela
)

st.title("📊 Gráficos no Streamlit — Aula Completa")
st.markdown("Navegue pelas abas para acompanhar cada bloco da aula.")


# =============================================================================
# ███████████████████████████████████████████████████████████
# DADOS COMPARTILHADOS — usados em vários blocos
# ███████████████████████████████████████████████████████████
# =============================================================================

# Dados de sensores IoT (mesmo contexto do arquivo Gradio)
dados_sensores = pd.DataFrame({
    "hora":        [0, 1, 2, 3, 4, 5, 6, 7, 8],
    "temperatura": [42, 45, 43, 50, 55, 52, 48, 47, 49],
    "vibração":    [0.1, 0.2, 0.15, 0.4, 0.5, 0.45, 0.3, 0.25, 0.28],
    "motor":       ["M1", "M1", "M1", "M2", "M2", "M2", "M3", "M3", "M3"],
})


# =============================================================================
# ███████████████████████████████████████████████████████████
# BLOCO 4 — FUNÇÕES AUXILIARES (definidas antes do layout)
# Precisam estar definidas antes de serem chamadas
# ███████████████████████████████████████████████████████████
# =============================================================================

@st.cache_data   # Cache: baixa a imagem UMA vez e reutiliza nas re-execuções
def carregar_imagem_fundo():
    """
    Baixa e retorna uma imagem de exemplo para usar como fundo de gráfico.
    @st.cache_data evita re-download a cada interação do usuário.
    """
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    try:
        with urllib.request.urlopen(url, timeout=5) as resposta:
            bytes_imagem = resposta.read()
        imagem_pil = Image.open(io.BytesIO(bytes_imagem)).convert("RGB")
        return np.array(imagem_pil)
    except Exception:
        # Fallback sintético se o download falhar
        imagem_sintetica = np.zeros((200, 300, 3), dtype=np.uint8)
        imagem_sintetica[:, :, 0] = 200
        return imagem_sintetica


def grafico_matplotlib_com_fundo(ponto_x, ponto_y):
    """
    Plota um gráfico Matplotlib com imagem de fundo no plano cartesiano.

    CONCEITO CHAVE — extent:
      ax.imshow(imagem, extent=[x_esq, x_dir, y_baixo, y_cima])
      Define em quais COORDENADAS CARTESIANAS a imagem será renderizada.
      Depois você plota pontos normalmente — eles aparecem sobre a imagem.
    """
    imagem_fundo = carregar_imagem_fundo()
    x_min, x_max = 0, 10
    y_min, y_max = 0, 10

    figura, eixo = plt.subplots(figsize=(7, 6))

    # ── CHAVE: imshow com extent ──────────────────────────────────────────────
    # extent=[esquerda, direita, baixo, cima] em unidades do EIXO CARTESIANO
    # aspect="auto" → a imagem se estica para preencher o espaço sem distorcer o eixo
    # zorder=0 → imagem fica ATRÁS de tudo que será plotado em seguida
    eixo.imshow(
        imagem_fundo,
        extent=[x_min, x_max, y_min, y_max],
        aspect="auto",
        origin="upper",   # linha 0 da imagem = topo do extent
        zorder=0,
        alpha=0.6,
    )

    # Pontos fixos (sensores existentes) — plotados SOBRE a imagem
    sensores_x = [2.0, 5.0, 8.0, 3.5]
    sensores_y = [3.0, 7.0, 2.0, 6.5]
    eixo.scatter(sensores_x, sensores_y, color="yellow", s=120, zorder=2,
                 marker="^", edgecolors="black", linewidths=1, label="Sensores fixos")

    # Ponto do usuário (controlado pelo slider)
    eixo.scatter(ponto_x, ponto_y, color="red", s=200, zorder=2,
                 label=f"Novo sensor ({ponto_x:.1f}, {ponto_y:.1f})",
                 edgecolors="white", linewidths=2)

    eixo.set_xlim(x_min, x_max)
    eixo.set_ylim(y_min, y_max)
    eixo.set_xlabel("Posição X (metros)")
    eixo.set_ylabel("Posição Y (metros)")
    eixo.set_title("Planta da Fábrica — Posicionamento de Sensores")
    eixo.legend(loc="upper right")
    eixo.grid(True, alpha=0.3, zorder=1)
    figura.tight_layout()

    return figura


# Posições de alertas para o Bloco 5 (proporção 0.0 a 1.0 do tamanho da imagem)
POSICOES_ALERTAS = [
    {"cx": 0.25, "cy": 0.30, "raio": 0.04, "cor": (255, 0, 0, 180),   "label": "Alarme crítico"},
    {"cx": 0.60, "cy": 0.55, "raio": 0.03, "cor": (255, 200, 0, 180), "label": "Atenção"},
    {"cx": 0.80, "cy": 0.20, "raio": 0.03, "cor": (0, 200, 0, 180),   "label": "Normal"},
]


def desenhar_bolas_na_imagem(imagem_pil):
    """
    Recebe uma imagem PIL, desenha círculos coloridos sobre ela e retorna.

    TÉCNICA:
      1. Converte para RGBA (suporta transparência)
      2. Cria overlay transparente separado
      3. Desenha círculos no overlay com ImageDraw
      4. Combina overlay + imagem com alpha_composite
      5. Retorna como RGB
    """
    if imagem_pil is None:
        imagem_pil = Image.new("RGB", (640, 480), color=(180, 180, 180))

    imagem_rgba = imagem_pil.convert("RGB").convert("RGBA")
    largura, altura = imagem_rgba.size

    # Camada transparente onde os círculos serão desenhados
    overlay = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    caneta = ImageDraw.Draw(overlay)

    for alerta in POSICOES_ALERTAS:
        # Converte proporção para pixels reais
        cx = int(alerta["cx"] * largura)
        cy = int(alerta["cy"] * altura)
        raio = int(alerta["raio"] * min(largura, altura))

        # ellipse recebe [(x_esquerda, y_topo), (x_direita, y_base)]
        caneta.ellipse(
            [(cx - raio, cy - raio), (cx + raio, cy + raio)],
            fill=alerta["cor"],
            outline=(255, 255, 255, 255),
            width=3,
        )
        caneta.text(
            (cx - raio, cy + raio + 4),
            alerta["label"],
            fill=(255, 255, 255, 230),
        )

    # Combina overlay com a imagem original respeitando transparência
    resultado = Image.alpha_composite(imagem_rgba, overlay)
    return resultado.convert("RGB")


# =============================================================================
# ███████████████████████████████████████████████████████████
# LAYOUT PRINCIPAL — abas por bloco
#
# DIFERENÇA DO GRADIO:
#   Gradio usa gr.Tab() dentro de gr.Blocks()
#   Streamlit usa st.tabs() que retorna uma lista de contextos
# ███████████████████████████████████████████████████████████
# =============================================================================

# st.tabs retorna uma lista — cada item é um contexto de aba
aba1, aba2, aba3, aba4, aba5, aba_resumo = st.tabs([
    "1 — Nativos",
    "2 — Matplotlib",
    "3 — Plotly",
    "4 — Imagem de Fundo",
    "5 — Bolas sobre Imagem",
    "📋 Resumo",
])


# =============================================================================
# ██████████████████████████████████████████████████████████████████
# ABA 1 — GRÁFICOS NATIVOS DO STREAMLIT
#
# COMPONENTES:
#   st.line_chart(df)      → linha
#   st.bar_chart(df)       → barras
#   st.scatter_chart(df)   → pontos
#
# DIFERENÇA DO GRADIO:
#   Gradio: gr.LinePlot(df, x="hora", y="temperatura")
#   Streamlit: precisa indexar o DataFrame por x antes de passar
#              OU usar o parâmetro x= e y= (disponível nas versões recentes)
# ██████████████████████████████████████████████████████████████████
# =============================================================================

with aba1:
    st.markdown("""
    ### Componentes Nativos: `st.line_chart`, `st.bar_chart`, `st.scatter_chart`
    - Recebem um **pandas DataFrame** com o index ou coluna como eixo X
    - Zero configuração para casos simples
    - Interatividade embutida: zoom, pan, hover
    - Para séries múltiplas: cada coluna numérica vira uma série
    """)

    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.markdown("**1A — line_chart: temperatura × hora**")

        # Prepara o DataFrame para o gráfico de linha:
        # st.line_chart usa o index como eixo X por padrão
        df_linha = dados_sensores.set_index("hora")[["temperatura"]]
        st.line_chart(df_linha)

    with col_dir:
        st.markdown("**1B — line_chart com múltiplas séries por motor**")

        # Para séries múltiplas, usa o parâmetro color= (Streamlit >= 1.26)
        # Cada valor único de 'motor' vira uma cor/série
        st.line_chart(
            dados_sensores,
            x="hora",
            y="temperatura",
            color="motor",
        )

    col_esq2, col_dir2 = st.columns(2)

    with col_esq2:
        st.markdown("**1C — scatter_chart: Temperatura × Vibração**")
        st.scatter_chart(
            dados_sensores,
            x="temperatura",
            y="vibração",
            color="motor",
        )

    with col_dir2:
        st.markdown("**1D — bar_chart: Temperatura média por Motor**")

        # bar_chart não tem y_aggregate nativo — calculamos antes
        df_media = dados_sensores.groupby("motor")["temperatura"].mean().reset_index()
        df_media.columns = ["Motor", "Temperatura Média (°C)"]
        st.bar_chart(df_media, x="Motor", y="Temperatura Média (°C)")

    st.markdown("---")
    st.markdown("**1E — line_chart interativo: filtrado por selectbox**")
    st.markdown("""
    > **Como funciona no Streamlit:** quando o usuário muda o selectbox,
    > o script inteiro re-executa. O `if` abaixo filtra o DataFrame
    > na re-execução e o gráfico aparece já atualizado — sem callback explícito.
    """)

    # selectbox retorna o valor selecionado diretamente
    motor_selecionado = st.selectbox(
        label="Filtrar por Motor",
        options=["Todos", "M1", "M2", "M3"],
    )

    # Filtra o DataFrame com base na seleção atual
    if motor_selecionado == "Todos":
        df_filtrado = dados_sensores
    else:
        df_filtrado = dados_sensores[dados_sensores["motor"] == motor_selecionado]

    # Gráfico renderizado com os dados já filtrados
    st.line_chart(df_filtrado, x="hora", y="temperatura")


# =============================================================================
# ██████████████████████████████████████████████████████████████████
# ABA 2 — MATPLOTLIB VIA st.pyplot
#
# COMO FUNCIONA:
#   1. Crie uma figura Matplotlib normalmente (plt.subplots)
#   2. Chame st.pyplot(figura) para exibi-la
#
# DIFERENÇA DO GRADIO:
#   Gradio: gr.Plot() como output + função retorna figura
#   Streamlit: st.pyplot(figura) chamado diretamente no fluxo do script
# ██████████████████████████████████████████████████████████████████
# =============================================================================

with aba2:
    st.markdown("""
    ### `st.pyplot` com Matplotlib
    - Crie a figura com `plt.subplots()` e passe para `st.pyplot(fig)`
    - Controle total: cores, fontes, subplots, anotações, imshow
    - Re-executa automaticamente quando os widgets mudam
    """)

    st.markdown("#### 2A — Gráfico fixo")

    # Cria a figura diretamente no corpo do script
    tempo_fixo = np.linspace(0, 4 * np.pi, 300)
    sinal_fixo = np.sin(tempo_fixo) * np.exp(-tempo_fixo / 10)

    figura_fixa, eixo_fixo = plt.subplots(figsize=(8, 3))
    eixo_fixo.plot(tempo_fixo, sinal_fixo, color="#E84393", linewidth=2, label="Sinal de vibração")
    eixo_fixo.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    eixo_fixo.set_title("Sinal de Vibração Amortecida")
    eixo_fixo.set_xlabel("Tempo (rad)")
    eixo_fixo.set_ylabel("Amplitude")
    eixo_fixo.legend()
    figura_fixa.tight_layout()

    # st.pyplot exibe a figura no lugar onde foi chamado
    st.pyplot(figura_fixa)
    plt.close(figura_fixa)   # Boa prática: libera memória após exibir

    st.markdown("#### 2B — Gráfico controlado por Sliders")
    st.markdown("""
    > Os sliders abaixo controlam a onda. Cada vez que você move um slider,
    > o Streamlit re-executa o script, recalcula o gráfico e exibe o novo resultado.
    """)

    col_freq, col_amp = st.columns(2)

    with col_freq:
        # st.slider retorna o valor atual — disponível imediatamente na linha seguinte
        frequencia = st.slider(
            label="Frequência da onda",
            min_value=0.5, max_value=5.0, value=1.0, step=0.1,
        )

    with col_amp:
        amplitude = st.slider(
            label="Amplitude",
            min_value=1.0, max_value=8.0, value=3.0, step=0.5,
        )

    # Usa os valores atuais dos sliders para gerar o gráfico
    tempo_dinamico = np.linspace(0, 2 * np.pi, 400)
    sinal_dinamico = amplitude * np.sin(frequencia * tempo_dinamico)

    figura_dinamica, eixo_dinamico = plt.subplots(figsize=(8, 3))
    eixo_dinamico.plot(tempo_dinamico, sinal_dinamico, color="#0073e6", linewidth=2)
    eixo_dinamico.set_ylim(-10, 10)
    eixo_dinamico.set_title(f"Onda: frequência={frequencia:.1f}, amplitude={amplitude:.1f}")
    eixo_dinamico.set_xlabel("Tempo (rad)")
    eixo_dinamico.set_ylabel("Amplitude")
    figura_dinamica.tight_layout()

    st.pyplot(figura_dinamica)
    plt.close(figura_dinamica)


# =============================================================================
# ██████████████████████████████████████████████████████████████████
# ABA 3 — PLOTLY VIA st.plotly_chart
#
# COMO FUNCIONA:
#   1. Crie uma figura Plotly (px ou go)
#   2. Chame st.plotly_chart(figura) para exibi-la
#   3. use_container_width=True → gráfico usa toda a largura da coluna
#
# DIFERENÇA DO GRADIO:
#   Gradio: gr.Plot() genérico para qualquer biblioteca
#   Streamlit: st.plotly_chart() específico para Plotly
# ██████████████████████████████████████████████████████████████████
# =============================================================================

with aba3:
    st.markdown("""
    ### `st.plotly_chart` com Plotly
    - `plotly.express` → API de alto nível, baseada em DataFrame
    - `plotly.graph_objects` → controle total de cada elemento
    - Zoom, hover, pan, download nativos — sem configuração extra
    """)

    st.markdown("#### 3A — plotly.express: múltiplas séries")

    # Gera dados de temperatura dos 3 motores ao longo de 24 horas
    df_plotly = pd.DataFrame({
        "hora":        list(range(24)) * 3,
        "temperatura": (
            [40 + int(v) for v in np.random.randint(-3, 3, 24)] +
            [50 + int(v) for v in np.random.randint(-3, 3, 24)] +
            [35 + int(v) for v in np.random.randint(-3, 3, 24)]
        ),
        "motor": ["Motor A"] * 24 + ["Motor B"] * 24 + ["Motor C"] * 24,
    })

    # px.line: uma linha por valor único de color=
    figura_px = px.line(
        df_plotly,
        x="hora",
        y="temperatura",
        color="motor",
        title="Temperatura ao longo do dia — 3 Motores",
        labels={"hora": "Hora do dia", "temperatura": "Temperatura (°C)"},
        template="plotly_white",
    )
    # use_container_width=True → gráfico preenche toda a coluna/tela
    st.plotly_chart(figura_px, use_container_width=True)

    st.markdown("#### 3B — Gauge (velocímetro) com graph_objects")

    # Slider para controlar o valor exibido no gauge
    temperatura_gauge = st.slider(
        label="Temperatura atual do sensor (°C)",
        min_value=0, max_value=100, value=55, step=1,
    )

    # go.Indicator: componente de gauge do Plotly
    figura_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=temperatura_gauge,
        delta={"reference": 45},
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
                "value": 70,
            },
        },
    ))
    figura_gauge.update_layout(height=350)
    st.plotly_chart(figura_gauge, use_container_width=True)

    st.markdown("#### 3C — Superfície 3D interativa")

    # go.Surface: grade 3D onde Z é renderizado como superfície colorida
    x_vals = np.linspace(-3, 3, 20)
    y_vals = np.linspace(-3, 3, 20)
    X, Y = np.meshgrid(x_vals, y_vals)
    Z = np.sin(np.sqrt(X**2 + Y**2)) * 30 + 50   # Valores ~20°C a ~80°C

    figura_3d = go.Figure(go.Surface(
        z=Z, x=X, y=Y,
        colorscale="RdYlGn_r",
        colorbar={"title": "°C"},
    ))
    figura_3d.update_layout(
        title="Mapa de Calor 3D do Motor",
        scene={
            "xaxis_title": "Posição X",
            "yaxis_title": "Posição Y",
            "zaxis_title": "Temperatura (°C)",
        },
        height=500,
    )
    st.plotly_chart(figura_3d, use_container_width=True)


# =============================================================================
# ██████████████████████████████████████████████████████████████████
# ABA 4 — IMAGEM DE FUNDO NO PLANO CARTESIANO
#
# TÉCNICA:
#   ax.imshow(array_numpy, extent=[x0, x1, y0, y1])
#   extent mapeia as coordenadas da imagem para o sistema cartesiano
#   Depois você plota normalmente com scatter(), plot(), etc.
# ██████████████████████████████████████████████████████████████████
# =============================================================================

with aba4:
    st.markdown("""
    ### Matplotlib: imagem de fundo no plano cartesiano
    - `ax.imshow(imagem, extent=[x0, x1, y0, y1])` posiciona a imagem
      dentro de coordenadas **cartesianas** (não pixels)
    - `extent` é o que alinha a imagem com os eixos numéricos
    - `aspect="auto"` permite que a imagem distorça para preencher o extent
    - Depois você plota pontos, linhas etc. normalmente **sobre** a imagem
    - Caso de uso: planta de fábrica com sensores em coordenadas métricas
    """)

    col_x, col_y = st.columns(2)

    with col_x:
        novo_sensor_x = st.slider("X do novo sensor", 0.0, 10.0, 4.0, 0.5)

    with col_y:
        novo_sensor_y = st.slider("Y do novo sensor", 0.0, 10.0, 4.0, 0.5)

    # A função já usa @st.cache_data na imagem de fundo — apenas o gráfico é recriado
    figura_fundo = grafico_matplotlib_com_fundo(novo_sensor_x, novo_sensor_y)
    st.pyplot(figura_fundo)
    plt.close(figura_fundo)


# =============================================================================
# ██████████████████████████████████████████████████████████████████
# ABA 5 — BOLAS SOBRE IMAGEM COM PIL
#
# DIFERENÇA DO BLOCO 4:
#   Bloco 4 = plano cartesiano com imagem de fundo (unidades métricas)
#   Bloco 5 = edição direta de pixels da imagem (unidades em pixels)
#
# STREAMLIT vs GRADIO:
#   Gradio: gr.Image com .select() captura coordenadas do clique
#   Streamlit: st.image apenas exibe; para captura de clique precisa
#              de st.file_uploader + processamento manual.
#              Usamos st.file_uploader + botão para este bloco.
# ██████████████████████████████████████████████████████████████████
# =============================================================================

with aba5:
    st.markdown("""
    ### `st.image` + PIL: desenhar círculos diretamente nos pixels
    - `st.file_uploader` recebe a imagem do usuário
    - `Image.open()` converte para PIL
    - `ImageDraw.Draw(imagem)` abre um "lápis" para desenhar
    - `caneta.ellipse([(x0,y0),(x1,y1)])` desenha círculo/elipse
    - Coordenadas em **pixels** — diferente do Bloco 4 (coordenadas métricas)
    - Técnica: overlay RGBA + `alpha_composite` = círculos com transparência
    """)

    st.markdown("#### 5A — Bolas fixas pré-definidas (alertas de sensor)")
    st.markdown("Faça upload de uma imagem — os alertas serão desenhados em posições relativas (%):")

    # st.file_uploader retorna None até o usuário enviar algo
    arquivo_enviado = st.file_uploader(
        label="Envie uma imagem",
        type=["png", "jpg", "jpeg"],
        key="upload_5a",
    )

    # Botão para acionar o processamento
    if st.button("Desenhar alertas na imagem", type="primary"):
        # Abre a imagem com PIL a partir dos bytes recebidos
        if arquivo_enviado is not None:
            imagem_recebida = Image.open(arquivo_enviado)
        else:
            # Sem upload: cria imagem cinza padrão para demonstração
            imagem_recebida = Image.new("RGB", (640, 480), color=(180, 180, 180))

        imagem_com_alertas = desenhar_bolas_na_imagem(imagem_recebida)

        col_antes, col_depois = st.columns(2)

        with col_antes:
            st.markdown("**Antes**")
            st.image(imagem_recebida, use_container_width=True)

        with col_depois:
            st.markdown("**Depois**")
            # st.image aceita PIL.Image diretamente
            st.image(imagem_com_alertas, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 5B — Marcar posição manualmente com sliders")
    st.markdown("""
    > **Nota:** Streamlit não captura cliques em imagens nativamente
    > (diferente do `gr.Image.select()` do Gradio). A alternativa idiomática
    > é usar sliders para o usuário informar as coordenadas X e Y em pixels.
    """)

    arquivo_5b = st.file_uploader(
        label="Envie uma imagem para marcar ponto",
        type=["png", "jpg", "jpeg"],
        key="upload_5b",
    )

    # Define os limites dos sliders baseado no tamanho da imagem
    if arquivo_5b is not None:
        imagem_5b = Image.open(arquivo_5b)
        largura_5b, altura_5b = imagem_5b.size
    else:
        imagem_5b = Image.new("RGB", (640, 480), color=(180, 180, 180))
        largura_5b, altura_5b = 640, 480

    col_px, col_py = st.columns(2)

    with col_px:
        pixel_x = st.slider("Posição X (pixels)", 0, largura_5b - 1, largura_5b // 2)

    with col_py:
        pixel_y = st.slider("Posição Y (pixels)", 0, altura_5b - 1, altura_5b // 2)

    # Desenha a bola no ponto especificado pelos sliders
    imagem_5b_rgba = imagem_5b.convert("RGB").convert("RGBA")
    overlay_5b = Image.new("RGBA", imagem_5b_rgba.size, (0, 0, 0, 0))
    caneta_5b = ImageDraw.Draw(overlay_5b)
    raio_5b = 20

    caneta_5b.ellipse(
        [(pixel_x - raio_5b, pixel_y - raio_5b), (pixel_x + raio_5b, pixel_y + raio_5b)],
        fill=(0, 120, 255, 200),
        outline=(255, 255, 255, 255),
        width=3,
    )

    imagem_com_ponto = Image.alpha_composite(imagem_5b_rgba, overlay_5b).convert("RGB")
    st.image(imagem_com_ponto, caption=f"Ponto marcado em ({pixel_x}, {pixel_y})", use_container_width=True)


# =============================================================================
# ██████████████████████████████████████████████████████████████████
# ABA RESUMO
# ██████████████████████████████████████████████████████████████████
# =============================================================================

with aba_resumo:
    st.markdown("""
    ## Mapa mental da aula

    | Componente Streamlit | Equivalente Gradio | Quando usar |
    |---|---|---|
    | `st.line_chart` | `gr.LinePlot` | Série temporal, tendência |
    | `st.scatter_chart` | `gr.ScatterPlot` | Correlação entre variáveis |
    | `st.bar_chart` | `gr.BarPlot` | Comparação categórica |
    | `st.pyplot(fig)` | `gr.Plot` + Matplotlib | Gráfico customizado |
    | `st.plotly_chart(fig)` | `gr.Plot` + Plotly | Interatividade rica, gauge, 3D |
    | `st.pyplot` + `imshow` | `gr.Plot` + imagem de fundo | Coordenadas reais sobre imagem |
    | `st.image` + PIL | `gr.Image` + PIL | Edição de pixels, anotações |

    ## Diferença fundamental: modelo de execução

    | Gradio | Streamlit |
    |---|---|
    | Interface declarativa montada uma vez | Script re-executa a cada interação |
    | Callbacks explícitos (`.change()`, `.click()`) | Sem callbacks — lê widgets inline |
    | `demo.load()` para inicializar gráficos | Gráficos gerados no corpo do script |
    | `gr.State` para compartilhar dados | `st.session_state` para persistir entre re-execuções |

    ## Referências
    - [Streamlit — Chart elements](https://docs.streamlit.io/develop/api-reference/charts)
    - [Streamlit — st.pyplot](https://docs.streamlit.io/develop/api-reference/charts/st.pyplot)
    - [Streamlit — st.plotly_chart](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart)
    - [Matplotlib imshow](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.imshow.html)
    - [Plotly Express](https://plotly.com/python/plotly-express/)
    - [PIL ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
    """)
