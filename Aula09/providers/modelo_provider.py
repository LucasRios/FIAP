# =============================================================================
# providers/modelo_provider.py — Fonte de verdade do modelo de linguagem
#
# Responsabilidade: tudo que diz respeito ao modelo fica aqui.
# O resto do sistema não sabe se o modelo é simulado, OpenAI ou local.
# Para trocar de provedor (ex: simulação → OpenAI), edite apenas este arquivo.
# =============================================================================

import random


def calcular_confianca(pergunta: str) -> float:
    """
    Estima a confiança do modelo com base na pergunta recebida.

    Em produção: substitua por logprobs da API ou outra métrica real.
    Aqui usamos comprimento da pergunta como proxy — perguntas mais
    específicas tendem a gerar contexto mais rico para o modelo.

    Retorna um float entre 0.0 e 1.0.
    """
    if len(pergunta) > 50:
        return round(random.uniform(0.78, 0.95), 2)
    elif len(pergunta) > 20:
        return round(random.uniform(0.55, 0.77), 2)
    else:
        return round(random.uniform(0.30, 0.54), 2)


def chamar_modelo(pergunta: str, historico: list) -> tuple[str, float]:
    """
    Chama o modelo de linguagem e retorna resposta + confiança.

    Parâmetros:
        pergunta:  mensagem atual do usuário
        historico: lista de pares [pergunta, resposta] — conversa anterior

    Retorna:
        (resposta_completa: str, confianca: float)

    Para integrar com OpenAI, substitua o bloco de simulação por:
        client = openai.OpenAI()
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=_converter_historico(historico) + [{"role": "user", "content": pergunta}],
            stream=True
        )
        resposta = "".join(chunk.choices[0].delta.content or "" for chunk in stream)
    """
    confianca = calcular_confianca(pergunta)

    # Simulação de resposta — substitua por chamada real à API
    resposta = (
        "Compreendi sua pergunta. Com base no contexto fornecido, "
        "posso indicar que este é um sistema de demonstração que simula "
        "o comportamento de um modelo de linguagem generativo. "
        "Em uma implementação real, aqui estaria a resposta do seu modelo, "
        "gerada token por token via streaming."
    )

    return resposta, confianca
