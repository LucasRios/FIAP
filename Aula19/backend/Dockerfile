# 1. Imagem base: Linux mínimo com Python 3.12.10 já instalado
FROM python:3.12.10

# 2. Ajustes de comportamento do Python dentro do container
#    - PYTHONDONTWRITEBYTECODE: não gera arquivos .pyc (inúteis num container)
#    - PYTHONUNBUFFERED: envia os print() direto para os logs, sem atraso
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Usuário sem privilégios de administrador para rodar a aplicação
RUN useradd --create-home --uid 1000 forzy

# 4. Pasta de trabalho dentro do container
WORKDIR /app

# 5. Dependências primeiro — aproveita o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Código da aplicação (inclui o motor.db como banco inicial)
COPY --chown=forzy:forzy . .

# 7. O usuário forzy precisa poder escrever na pasta /app:
#    o SQLite cria arquivos temporários ao lado do motor.db durante as escritas
RUN chown forzy:forzy /app

# 8. A partir daqui, tudo roda como o usuário forzy
USER forzy

# 9. Documenta a porta em que a API escuta
EXPOSE 8000

# 10. Verificação de saúde: o Docker chama a rota "/" periodicamente
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# 11. Comando executado quando o container inicia
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]