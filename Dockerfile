FROM python:3.12-slim

WORKDIR /app

# Instala dependências de compilação do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Adiciona a pasta src ao caminho do Python
ENV PYTHONPATH=/app/src
ENV PORT=8080
EXPOSE 8080

# Executa o servidor FastAPI
CMD ["sh", "-c", "uvicorn mestre_ia.main:app --host 0.0.0.0 --port ${PORT}"]
