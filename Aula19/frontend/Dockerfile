# frontend/Dockerfile — imagem da interface Gradio do Forzy

FROM python:3.12.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # O Gradio lê estas variáveis automaticamente ao chamar launch():
    # escutar em todas as interfaces (obrigatório dentro de container) e na porta 7860
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

RUN useradd --create-home --uid 1000 forzy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=forzy:forzy . .

USER forzy

EXPOSE 7860

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/')" || exit 1

CMD ["python", "app.py"]