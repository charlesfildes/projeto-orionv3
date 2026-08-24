#!/bin/bash

BASE_DIR="/media/carlos/Arquivos/Orion/projeto-orion"

start_orion() {
    echo "⚡ Iniciando o Projeto Orion (Atena)..."
    if [ -f "$BASE_DIR/iniciar_orion.sh" ]; then
        cd "$BASE_DIR"
        bash "$BASE_DIR/iniciar_orion.sh"
    else
        echo "❌ Arquivo iniciar_orion.sh não encontrado em $BASE_DIR"
    fi
}

stop_orion() {
    echo "🛑 Desligando o Projeto Orion..."
    
    # Matar processos das portas 8000 e 8501
    fuser -k 8000/tcp 8501/tcp 2>/dev/null
    
    # Matar processos remanescentes do Python/Uvicorn/Streamlit
    PIDS=$(pgrep -f "uvicorn|streamlit|main.py")
    if [ -n "$PIDS" ]; then
        kill -9 $PIDS 2>/dev/null
    fi
    echo "✅ Projeto Orion desligado com sucesso!"
}

status_orion() {
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null || lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null ; then
        echo "🟢 Projeto Orion está ONLINE."
    else
        echo "🔴 Projeto Orion está OFFLINE."
    fi
}

case "$1" in
    start)
        start_orion
        ;;
    stop)
        stop_orion
        ;;
    status)
        status_orion
        ;;
    *)
        echo "Uso: $0 {start|stop|status}"
        exit 1
        ;;
esac
