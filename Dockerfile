FROM python:3.12-slim AS production

LABEL org.opencontainers.image.title="Projeto Orion — Plataforma Mestre-IA"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MESTRE_IA_AMBIENTE=prod

RUN groupadd --system mestre && useradd --system --gid mestre --create-home mestre
RUN mkdir -p /app/logs /app/dados && chown -R mestre:mestre /app

WORKDIR /app

# Copiar todos os arquivos necessários para o build
COPY requirements.txt .
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/

# Instalar dependências e o pacote
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/pip install . --no-deps

ENV PATH="/opt/venv/bin:$PATH"
USER mestre

# Health check usando Python diretamente (não depende de --version)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mestre_ia; print(mestre_ia.__version__)" || exit 1

# Porta reservada para futura REST API (V2)
# EXPOSE 8000

ENTRYPOINT ["mestre-ia"]
CMD ["--help"]
