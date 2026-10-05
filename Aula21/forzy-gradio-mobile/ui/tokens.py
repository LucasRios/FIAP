# =============================================================================
# ui/tokens.py — Design tokens do Forzy: a única fonte de verdade visual
#
# Três camadas, da mais bruta para a mais específica:
#
#   1. PRIMITIVOS   a paleta crua ("vermelho 700 é #991B1B"). Nenhum arquivo
#                   fora deste usa primitivos diretamente.
#   2. SEMÂNTICOS   o significado ("texto de crítico", "cor da ação"). É o que
#                   os componentes consomem. Existe uma versão clara e uma escura.
#   3. COMPONENTE   decisões de um componente específico ("altura mínima de
#                   um alvo de toque").
#
# Trocar a cor do alarme crítico em TODO o app = mudar uma linha aqui.
#
# Este arquivo também exporta os tokens para o formato que cada ferramenta
# entende: `python -m ui.tokens` gera o .streamlit/config.toml.
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Primitivos
# -----------------------------------------------------------------------------
PRIMITIVOS = {
    "branco": "#FFFFFF",
    "cinza": {
        50: "#F7F8FA", 100: "#EEF0F3", 200: "#DDE1E7", 400: "#7D8794",
        600: "#4B5563", 700: "#374151", 800: "#1F2933", 900: "#111827", 950: "#0E1117",
    },
    "azul": {300: "#93C5FD", 600: "#2563EB", 800: "#1E40AF", 950: "#172554"},
    "verde": {50: "#F0FDF4", 300: "#86EFAC", 600: "#16A34A", 800: "#166534", 950: "#052E16"},
    "ambar": {50: "#FFFBEB", 300: "#FCD34D", 600: "#D97706", 800: "#92400E", 950: "#451A03"},
    "vermelho": {50: "#FEF2F2", 300: "#FCA5A5", 600: "#DC2626", 800: "#991B1B", 950: "#450A0A"},
}

_c, _az, _vd, _am, _vm = (PRIMITIVOS[k] for k in ("cinza", "azul", "verde", "ambar", "vermelho"))

# -----------------------------------------------------------------------------
# 2. Semânticos — o mesmo vocabulário nos dois modos, valores diferentes
# -----------------------------------------------------------------------------
# Regra de ouro (herdada das IHMs industriais, norma ISA-101): o estado normal
# é discreto; a cor forte fica reservada para o que exige atenção. Por isso a
# cor da AÇÃO é azul, e não laranja: laranja disputaria com o âmbar do AVISO.
SEMANTICOS = {
    "claro": {
        "fundo": PRIMITIVOS["branco"],
        "superficie": _c[50],
        "borda": _c[400],          # 3:1 contra o fundo: limites de controle visíveis ao sol
        "borda_suave": _c[200],    # divisórias decorativas, não identificam controles
        "texto": _c[900],
        "texto_suave": _c[600],
        "acao": _az[800],
        "texto_sobre_acao": PRIMITIVOS["branco"],
        "normal_texto": _vd[800], "normal_fundo": _vd[50], "normal_destaque": _vd[600],
        "aviso_texto": _am[800], "aviso_fundo": _am[50], "aviso_destaque": _am[600],
        "critico_texto": _vm[800], "critico_fundo": _vm[50], "critico_destaque": _vm[600],
        "neutro_texto": _c[700], "neutro_fundo": _c[100], "neutro_destaque": _c[400],
    },
    "escuro": {
        "fundo": _c[950],
        "superficie": _c[900],
        "borda": _c[400],
        "borda_suave": _c[800],
        "texto": "#F3F4F6",
        "texto_suave": "#9CA3AF",
        # O Streamlit sempre escreve o texto do botão primário em BRANCO. Um azul
        # claro (300) parecia ótimo no escuro, mas deixava "branco sobre azul
        # claro" com 1,7:1. O token precisa refletir o que o framework renderiza.
        "acao": _az[600],
        "texto_sobre_acao": PRIMITIVOS["branco"],
        "normal_texto": _vd[300], "normal_fundo": _vd[950], "normal_destaque": _vd[600],
        "aviso_texto": _am[300], "aviso_fundo": _am[950], "aviso_destaque": _am[600],
        "critico_texto": _vm[300], "critico_fundo": _vm[950], "critico_destaque": _vm[600],
        "neutro_texto": "#D1D5DB", "neutro_fundo": _c[800], "neutro_destaque": _c[400],
    },
}

# Severidade da LEITURA (vem do back-end: normal | aviso | critico).
# Cada nível tem forma, ícone e texto próprios: a cor nunca é o único canal
# (daltonismo, tela ao sol, impressão em preto e branco).
SEVERIDADE = {
    "normal":   {"rotulo": "Normal",  "simbolo": "●", "icone": ":material/check_circle:", "cor_nativa": "green",  "peso": 0},
    "aviso":    {"rotulo": "Aviso",   "simbolo": "▲", "icone": ":material/warning:",      "cor_nativa": "orange", "peso": 1},
    "critico":  {"rotulo": "Crítico", "simbolo": "◆", "icone": ":material/error:",        "cor_nativa": "red",    "peso": 2},
    "sem_dado": {"rotulo": "Sem dado", "simbolo": "○", "icone": ":material/help:",        "cor_nativa": "gray",   "peso": -1},
}

# Status OPERACIONAL (vem do cadastro). É outro conceito, então tem outra
# linguagem visual: neutra, sem semáforo. Um motor "Operacional" com
# temperatura crítica não pode exibir verde em lugar nenhum da tela.
STATUS_OPERACIONAL = {
    "Operacional":   {"icone": ":material/power:",          "cor_nativa": "blue"},
    "Em Manutenção": {"icone": ":material/build:",          "cor_nativa": "violet"},
    "Desligado":     {"icone": ":material/power_settings_new:", "cor_nativa": "gray"},
}

# -----------------------------------------------------------------------------
# 3. Escalas e decisões de componente
# -----------------------------------------------------------------------------
ESPACO = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}   # grade de 4 px
RAIO = {"sm": 8, "md": 12, "lg": 16, "pilula": 999}
TIPO = {
    "base_px": 16,                                   # nunca menos: o iOS dá zoom em campos < 16 px
    "titulos_rem": ["1.5rem", "1.25rem", "1.125rem"],  # h1–h3 compactos para tela pequena
    "valor_metrica_rem": "1.75rem",
}
TOQUE = {"alvo_minimo_px": 48}                       # Material: 48 dp · Apple: 44 pt · WCAG AA: 24 px
BREAKPOINT = {"compacto_px": 600, "medio_px": 840}   # classes de janela do Material 3


# -----------------------------------------------------------------------------
# Funções auxiliares
# -----------------------------------------------------------------------------
def cores(modo: str = "claro") -> dict:
    """Tokens semânticos do modo pedido ('claro' ou 'escuro'; aceita 'light'/'dark')."""
    return SEMANTICOS["escuro" if modo in ("escuro", "dark") else "claro"]


def severidade(chave: str | None) -> dict:
    """Metadados visuais de uma severidade; chaves desconhecidas viram 'sem_dado'."""
    return SEVERIDADE.get(chave or "sem_dado", SEVERIDADE["sem_dado"])


def pior_severidade(*chaves: str) -> str:
    """A severidade mais grave entre várias leituras — usada no status-resumo do motor."""
    validas = [c for c in chaves if c in SEVERIDADE and c != "sem_dado"]
    return max(validas, key=lambda c: SEVERIDADE[c]["peso"]) if validas else "sem_dado"


def contraste(cor_a: str, cor_b: str) -> float:
    """Razão de contraste WCAG 2.x entre duas cores hexadecimais (1 a 21)."""
    def luminancia(hexa: str) -> float:
        hexa = hexa.lstrip("#")
        canais = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    maior, menor = sorted((luminancia(cor_a), luminancia(cor_b)), reverse=True)
    return (maior + 0.05) / (menor + 0.05)


def verificar_contrastes() -> list[str]:
    """
    Confere os pares de cor que o app realmente usa contra os mínimos do WCAG:
    4,5:1 para texto e 3:1 para limites de componentes (1.4.3 e 1.4.11).

    Devolve a lista de violações — vazia quando o tema está aprovado.
    É um teste automatizado do design system: rode antes de mudar uma cor.
    """
    problemas = []
    for modo, t in SEMANTICOS.items():
        pares_texto = [("texto", "fundo"), ("texto_suave", "fundo"), ("texto_sobre_acao", "acao"),
                       ("normal_texto", "normal_fundo"), ("aviso_texto", "aviso_fundo"),
                       ("critico_texto", "critico_fundo"), ("neutro_texto", "neutro_fundo")]
        for frente, fundo in pares_texto:
            r = contraste(t[frente], t[fundo])
            if r < 4.5:
                problemas.append(f"[{modo}] texto {frente}/{fundo} = {r:.2f}:1 (mínimo 4,5)")
        for limite in ("borda", "acao", "critico_destaque"):
            r = contraste(t[limite], t["fundo"])
            if r < 3:
                problemas.append(f"[{modo}] limite {limite}/fundo = {r:.2f}:1 (mínimo 3)")
    return problemas


def exportar_tema_streamlit() -> str:
    """
    Gera o .streamlit/config.toml a partir dos tokens.

    O [theme] do Streamlit É um arquivo de tokens: cada chave abaixo recebe um
    token semântico. As cores green/orange/red/gray/blue/violet são as que
    st.badge, st.success, st.warning e st.error usam — por isso os componentes
    nativos passam a falar a mesma língua visual dos nossos.
    """
    def bloco_cores(t: dict) -> list[str]:
        return [
            f'primaryColor = "{t["acao"]}"',
            f'backgroundColor = "{t["fundo"]}"',
            f'secondaryBackgroundColor = "{t["superficie"]}"',
            f'textColor = "{t["texto"]}"',
            f'borderColor = "{t["borda"]}"',
            f'greenColor = "{t["normal_destaque"]}"',
            f'greenBackgroundColor = "{t["normal_fundo"]}"',
            f'greenTextColor = "{t["normal_texto"]}"',
            f'orangeColor = "{t["aviso_destaque"]}"',
            f'orangeBackgroundColor = "{t["aviso_fundo"]}"',
            f'orangeTextColor = "{t["aviso_texto"]}"',
            f'redColor = "{t["critico_destaque"]}"',
            f'redBackgroundColor = "{t["critico_fundo"]}"',
            f'redTextColor = "{t["critico_texto"]}"',
            f'grayColor = "{t["neutro_destaque"]}"',
            f'grayBackgroundColor = "{t["neutro_fundo"]}"',
            f'grayTextColor = "{t["neutro_texto"]}"',
        ]

    linhas = [
        "# Gerado por `python -m ui.tokens` — não edite à mão; edite ui/tokens.py.",
        "",
        "[client]",
        'toolbarMode = "minimal"        # some o "Deploy" e o menu de dev: 90 px a mais de conteúdo',
        "",
        "[theme]",
        f"baseFontSize = {TIPO['base_px']}",
        f'baseRadius = "{RAIO["md"]}px"',
        f'buttonRadius = "{RAIO["sm"]}px"',
        f"headingFontSizes = {TIPO['titulos_rem']}".replace("'", '"'),
        f'metricValueFontSize = "{TIPO["valor_metrica_rem"]}"',
        "showWidgetBorder = true          # limite visível em todo campo: essencial ao sol",
        "",
        "[theme.light]",
        *bloco_cores(SEMANTICOS["claro"]),
        "",
        "[theme.dark]",
        *bloco_cores(SEMANTICOS["escuro"]),
        "",
    ]
    return "\n".join(linhas)


if __name__ == "__main__":
    import sys

    falhas = verificar_contrastes()
    if falhas:
        print("Contraste reprovado:\n  " + "\n  ".join(falhas), file=sys.stderr)
        sys.exit(1)
    print(exportar_tema_streamlit())
