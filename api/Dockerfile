# ---------- Imagem da API de Cadastro de Pets ----------
# Base oficial do Python, versão "slim" (enxuta)
FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE: não gera arquivos .pyc (lixo dentro da imagem)
# PYTHONUNBUFFERED: logs aparecem na hora no "docker logs" (sem ficar presos num buffer)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências primeiro (aproveita o cache: só reinstala se o requirements.txt mudar)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Depois o código
COPY app/ ./app/

# Segurança: roda como um usuário comum, e não como root (administrador)
# Se alguém invadir a app, não vira "dono" do container
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Uvicorn = o servidor que roda a app FastAPI, ouvindo em todas as interfaces na porta 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
