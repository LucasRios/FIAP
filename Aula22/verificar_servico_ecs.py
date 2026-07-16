# =============================================================================
# verificar_servico_ecs.py — Aula 22: verificando o status do Fargate via Python
#
# Responsabilidade: script simples de linha de comando (introdutório, um
# único arquivo) que consulta a AWS e mostra se o serviço ECS/Fargate do
# projeto está saudável — útil para checar o deploy sem precisar abrir o
# console da AWS toda vez.
#
# NOVO NESTA AULA: este arquivo inteiro, usando o cliente "ecs" do boto3
# (na Aula 21 usamos o cliente "bedrock-runtime" — mesma biblioteca,
# serviço diferente).
#
# Como instalar:
#   pip install boto3
#
# Como rodar:
#   python verificar_servico_ecs.py
# =============================================================================

import boto3

# Mesma ideia da Aula 21: nenhuma credencial escrita aqui. O boto3 usa a
# IAM Role da máquina onde este script roda (ou o "aws configure" local).
cliente_ecs = boto3.client("ecs", region_name="us-east-1")

NOME_DO_CLUSTER = "sprint-fiap-cluster"
NOME_DO_SERVICO = "sprint-backend-service"


def verificar_servico(cluster: str = NOME_DO_CLUSTER, servico: str = NOME_DO_SERVICO) -> None:
    """
    Consulta o ECS e imprime quantas tasks estão rodando, pendentes e
    desejadas para o serviço informado — os três números que indicam se
    o Fargate está com o serviço no tamanho esperado.
    """
    resposta = cliente_ecs.describe_services(cluster=cluster, services=[servico])

    servicos_encontrados = resposta.get("services", [])
    if not servicos_encontrados:
        print(f"Serviço '{servico}' não encontrado no cluster '{cluster}'.")
        return

    info = servicos_encontrados[0]

    print(f"Cluster:            {cluster}")
    print(f"Serviço:            {servico}")
    print(f"Status:             {info['status']}")
    print(f"Tasks desejadas:    {info['desiredCount']}")
    print(f"Tasks rodando:      {info['runningCount']}")
    print(f"Tasks pendentes:    {info['pendingCount']}")

    # Uma verificação simples de saúde: se o número de tasks rodando bate
    # com o desejado, o serviço está no tamanho esperado.
    if info["runningCount"] == info["desiredCount"]:
        print("\nServiço saudável: todas as tasks desejadas estão rodando.")
    else:
        print("\nAtenção: o número de tasks rodando é diferente do desejado.")


if __name__ == "__main__":
    verificar_servico()
