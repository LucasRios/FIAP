# =============================================================================
# backend/Dockerfile — Aula 19
# NOVO NESTA AULA: este arquivo inteiro. Define como o back-end FastAPI vira
# uma imagem Docker.
# =============================================================================

# Ponto de partida: imagem oficial do Python 3.11 (slim = menor tamanho)
FROM python:3.11-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia o requirements PRIMEIRO — aproveita o cache do Docker.
# Se o requirements não mudar, esta camada não é reconstruída a cada build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Só agora copia o restante do código
COPY . .

# Porta que o FastAPI vai usar dentro do container
EXPOSE 8000

# --host 0.0.0.0 é obrigatório: sem isso, o servidor só aceitaria conexões
# de dentro do próprio container, e o docker-compose não conseguiria acessá-lo.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
