# =============================================================================
# backend/aws_bedrock_provider.py — Aula 21: chamando a AWS sem senha no código
#
# Responsabilidade: mostrar a forma CORRETA de autenticar com serviços da AWS
# (aqui, o Bedrock — o serviço de modelos de IA da própria AWS) quando o
# código roda dentro de uma instância EC2 configurada com uma IAM Role.
#
# NOVO NESTA AULA: este arquivo inteiro. É um exemplo introdutório — por
# isso um único arquivo, sem pipeline/providers ainda.
#
# Pré-requisito (feito no CONSOLE da AWS, não no código):
#   1. IAM -> Roles -> Create Role -> Trusted entity: EC2
#   2. Adicionar a permissão "AmazonBedrockFullAccess" (ou mais restrita)
#   3. Na instância EC2 -> Actions -> Security -> Modify IAM Role -> selecionar a role
#
# Como instalar:
#   pip install boto3
# =============================================================================

import boto3


# -----------------------------------------------------------------------------
# ERRADO — NUNCA FAÇA ISSO (deixado aqui só como exemplo do que evitar)
# -----------------------------------------------------------------------------
# boto3.client(
#     "bedrock-runtime",
#     aws_access_key_id="AKIA...",        # <- vaza se o servidor for comprometido
#     aws_secret_access_key="segredo...", # <- nunca deve estar no código
# )


# -----------------------------------------------------------------------------
# CORRETO — usando a IAM Role da instância EC2 — NOVO NESTA AULA
# -----------------------------------------------------------------------------
# Quando o código roda DENTRO de uma instância EC2 que tem uma IAM Role
# associada, o boto3 encontra as credenciais automaticamente — sem
# precisarmos escrever nenhuma chave aqui. É o SDK "perguntando" para a
# própria infraestrutura da AWS: "quem sou eu, e o que posso fazer?".
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def chamar_modelo_bedrock(prompt: str, modelo_id: str = "anthropic.claude-haiku-4-5") -> str:
    """
    Envia um prompt para um modelo hospedado no Amazon Bedrock.

    Args:
        prompt: o texto de entrada para o modelo.
        modelo_id: identificador do modelo no Bedrock.

    Returns:
        O texto de resposta do modelo.

    Nota didática: esta função só funciona de verdade dentro de uma
    instância EC2 (ou outro serviço AWS) com a IAM Role configurada
    corretamente. Rodando localmente, sem uma role ou credenciais
    configuradas via "aws configure", o boto3 lançaria um erro de
    autenticação — o que é o comportamento esperado e desejado.
    """
    import json

    corpo = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
    })

    resposta = bedrock.invoke_model(modelId=modelo_id, body=corpo)
    resultado = json.loads(resposta["body"].read())

    return resultado["content"][0]["text"]
