# =============================================================================
# frontend/Dockerfile — Aula 19
# NOVO NESTA AULA: este arquivo inteiro.
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Porta padrão do Streamlit
EXPOSE 8501

# Healthcheck: o Docker verifica a cada 30s se o app está respondendo
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# --server.address=0.0.0.0 permite que o app aceite conexões de fora do container
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
