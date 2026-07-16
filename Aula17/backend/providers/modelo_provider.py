# =============================================================================
# backend/providers/modelo_provider.py — Aula 17
#
# Responsabilidade: chamar o modelo de IA para gerar resumo + sentimento
# numa única chamada, já instrumentado com metadata= (informação fixa que
# ajuda a filtrar e comparar versões no dashboard do LangSmith).
#
# NOVO NESTA AULA: o parâmetro metadata={...} no @traceable e o tratamento
# de resposta que não vem em JSON válido (o modelo pode "errar o formato").
# =============================================================================

import json
import anthropic
from langsmith import traceable

client = anthropic.Anthropic()


# metadata={...} — NOVO NESTA AULA: são informações FIXAS anexadas a todo
# trace desta função. Diferente das tags (rótulos livres), metadata costuma
# guardar dados estruturados, como qual modelo foi usado nesta versão.
@traceable(name="modelo_analisar_completo", metadata={"modelo": "claude-haiku-4-5-20251001"})
def analisar_completo(texto: str, entidades: list[str], session_id: str = None) -> dict:
    """
    Pede ao modelo um resumo + sentimento em uma única chamada, retornando
    um JSON estruturado.

    Args:
        texto: conteúdo da notícia já coletado.
        entidades: lista de entidades extraídas na etapa anterior do pipeline.
        session_id: usado apenas para aparecer no trace do LangSmith.

    Returns:
        dict com resumo, sentimento, confianca e tokens_usados.
    """
    prompt = f"""Analise a notícia abaixo e retorne um JSON com:
- resumo: resumo em 2 frases
- sentimento: "positivo", "negativo" ou "neutro"
- confianca: score de 0.0 a 1.0

Entidades identificadas: {', '.join(entidades)}

Notícia:
{texto[:2000]}

Retorne apenas o JSON, sem explicações."""

    resposta = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    conteudo = resposta.content[0].text.strip()

    try:
        resultado = json.loads(conteudo)
    except json.JSONDecodeError:
        # O modelo às vezes "foge" do formato JSON pedido. Em vez de deixar
        # o app quebrar, registramos um resultado seguro — e o LangSmith
        # vai mostrar esse trace com o conteúdo bruto, ajudando a investigar
        # depois por que o modelo não seguiu o formato.
        resultado = {"resumo": conteudo, "sentimento": "indefinido", "confianca": 0.0}

    resultado["tokens_usados"] = resposta.usage.input_tokens + resposta.usage.output_tokens
    return resultado
