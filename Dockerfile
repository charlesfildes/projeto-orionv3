FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala pacotes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação
COPY . .

ENV PYTHONPATH=/app/src
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn mestre_ia.main:app --host 0.0.0.0 --port ${PORT}"]
