# =============================================================================
# pipelines/chat_pipeline.py — Orquestração do fluxo de chat com streaming
#
# Responsabilidade: conectar as chamadas ao modelo com a lógica de streaming
# e a interpretação de confiança. Este é o único lugar que conhece tanto
# o provider de modelo quanto o provider de feedback.
#
# A UI chama apenas processar_mensagem() e registrar_feedback().
# Ela não sabe nada sobre como o modelo funciona ou onde o feedback é salvo.
# =============================================================================

import time

import providers.modelo_provider as modelo
import providers.feedback_provider as feedback


def _interpretar_confianca(confianca: float) -> tuple[str, str]:
    """
    Converte um score numérico em linguagem humana.

    Retorna uma tupla (descricao, nivel) para alimentar dois componentes
    distintos da interface — texto explicativo e indicador visual.
    """
    percentual = int(confianca * 100)

    if confianca >= 0.78:
        nivel = "🟢 Alta"
        descricao = f"Confiança: {percentual}% — O modelo tem alta certeza nesta resposta."
    elif confianca >= 0.55:
        nivel = "🟡 Média"
        descricao = f"Confiança: {percentual}% — Recomenda-se verificar informações importantes."
    else:
        nivel = "🔴 Baixa"
        descricao = f"Confiança: {percentual}% — Esta resposta pode conter imprecisões."

    return descricao, nivel


def processar_mensagem(pergunta: str, historico: list):
    """
    Gerador principal do chatbot — o coração do streaming.

    Este é o único lugar onde o `yield` acontece. A UI não implementa
    nenhuma lógica de streaming; ela apenas conecta este gerador a um
    componente gr.Chatbot.

    Fluxo:
        1. Validar entrada
        2. Chamar o modelo (provider) → obtém resposta + confiança
        3. Interpretar confiança em linguagem humana
        4. Simular geração token a token com yield progressivo
        5. Yield final com resposta completa para o sistema de feedback

    Yields: (historico_atual, descricao_confianca, nivel, resposta_completa)
    """
    if not pergunta.strip():
        yield historico, "", "", ""
        return

    resposta_completa, confianca = modelo.chamar_modelo(pergunta, historico)
    descricao, nivel = _interpretar_confianca(confianca)

    # Inicializar o histórico com a pergunta atual e resposta vazia
    # O Gradio atualiza o chatbot a cada yield desta lista
    historico_atual = historico + [
    {"role": "user", "content": pergunta},
    {"role": "assistant", "content": ""}
]

    # Streaming: acumular caractere a caractere e atualizar o chat
    # O padrão de acumulação (texto_parcial += c) é intencional:
    # sempre enviamos o texto COMPLETO até o momento, não apenas o novo fragmento.
    texto_parcial = ""
    for caractere in resposta_completa:
        texto_parcial += caractere
        historico_atual[-1]["content"] = texto_parcial
        yield historico_atual, descricao, nivel, resposta_completa
        time.sleep(0.015)

    # Yield final garante que a resposta completa chegue ao estado da UI
    yield historico_atual, descricao, nivel, resposta_completa


def registrar_feedback(pergunta: str, resposta: str, tipo: str) -> str:
    """
    Salva a avaliação do usuário e retorna uma mensagem de status formatada.

    Parâmetros:
        tipo: "positivo" ou "negativo"

    Retorna uma string pronta para exibir em um gr.Textbox de status.
    """
    feedback.salvar(pergunta, resposta, tipo)
    dados = feedback.resumo()

    if tipo == "positivo":
        return (
            f"✅ Feedback positivo registrado. "
            f"Total acumulado: {dados['total']} avaliações."
        )
    else:
        return (
            f"🔴 Feedback negativo registrado. "
            f"Total: {dados['total']} avaliações "
            f"({dados['positivos']} positivos, {dados['negativos']} negativos)."
        )
