#!/bin/bash

PROJETO_DIR="/media/carlos/Arquivos/Orion/projeto-orion"
VENV_PATH="/media/carlos/Arquivos/QPanda/.venv/bin/activate"

echo "🌌 Limpando processos antigos e iniciando Orion..."
fuser -k 8000/tcp 8501/tcp 2>/dev/null

cd "$PROJETO_DIR" || exit
source "$VENV_PATH"
export PYTHONPATH=$PYTHONPATH:"$PROJETO_DIR/src"

# Carrega a API Key do .env se existir
if [ -f .env ]; then
    export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY .env | cut -d '=' -f2)
fi

echo "🚀 Subindo a API FastAPI na porta 8000..."
uvicorn mestre_ia.main:app --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

sleep 3

trap "echo 'Encerrando serviços...'; kill $UVICORN_PID; exit" INT TERM EXIT

echo "💻 Subindo o Chat Streamlit na porta 8501..."
streamlit run src/mestre_ia/interfaces/web/app.py
