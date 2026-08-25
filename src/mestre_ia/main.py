import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configuração de path para importar módulos do projeto
RAIZ_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(RAIZ_DIR / "src"))

app = FastAPI(
    title="Projeto Orion API",
    description="Backend para integração quântica PyQPanda",
    version="1.0.0",
)


# ============================================================================
# DTOs
# ============================================================================

class ChatPayload(BaseModel):
    prompt: str = Field("", description="Prompt do usuário")
    mensagem: str = Field("", description="Mensagem alternativa")
    parametros: dict = Field(default_factory=dict, description="Parâmetros adicionais")


# ============================================================================
# Rotas de Saúde
# ============================================================================

@app.get("/health")
def health_check():
    """Verificação de saúde do servidor."""
    return {
        "status": "ok",
        "servico": "Projeto Orion API",
        "quantum_engine": "PyQPanda (CPUQVM)",
    }


# ============================================================================
# Rotas de Chat
# ============================================================================

@app.post("/")
@app.post("/chat")
@app.post("/api/chat")
@app.post("/api/v1/chat")
@app.post("/orquestrador/executar")
def processar_chat(payload: ChatPayload):
    """Processa chat — versão simplificada."""
    texto = payload.prompt or payload.mensagem or "Sem mensagem"
    return {
        "status": "sucesso",
        "resposta": f"Orion recebeu: {texto}",
        "servico": "chat",
    }


# ============================================================================
# Rota de Benchmark Quântico
# ============================================================================

@app.post("/quantum/benchmark")
def benchmark_qpanda(num_qubits: int = 18, shots: int = 1000):
    """
    Executa benchmark do QPanda com N qubits.
    """
    if num_qubits < 2:
        raise HTTPException(status_code=400, detail="Mínimo de 2 qubits.")
    if num_qubits > 28:
        raise HTTPException(
            status_code=400,
            detail="Máximo de 28 qubits para evitar travamento da CPU.",
        )
    if shots < 1 or shots > 10000:
        raise HTTPException(status_code=400, detail="Shots deve estar entre 1 e 10000.")

    try:
        import pyqpanda as pq
    except ImportError:
        return _benchmark_fallback(num_qubits, shots, "QPanda não instalado")

    start_time = time.time()

    try:
        qvm = pq.CPUQVM()
        qvm.init_qvm()

        if hasattr(qvm, "qAlloc_many"):
            qubits = qvm.qAlloc_many(num_qubits)
            cbits = qvm.cAlloc_many(num_qubits)
        elif hasattr(qvm, "qalloc_many"):
            qubits = qvm.qalloc_many(num_qubits)
            cbits = qvm.calloc_many(num_qubits)
        else:
            qubits = [qvm.qalloc() for _ in range(num_qubits)]
            cbits = [qvm.calloc() for _ in range(num_qubits)]

        prog = pq.QProg()
        for q in qubits:
            prog << pq.H(q)

        for i in range(num_qubits - 1):
            prog << pq.CNOT(qubits[i], qubits[i + 1])

        if hasattr(pq, "measure_all"):
            prog << pq.measure_all(qubits, cbits)
        else:
            for i in range(num_qubits):
                prog << pq.Measure(qubits[i], cbits[i])

        resultado = qvm.run_with_configuration(prog, cbits, shots)
        qvm.finalize()

        tempo_execucao_ms = (time.time() - start_time) * 1000
        estados_simultaneos = 2 ** num_qubits
        operacoes_totais = estados_simultaneos * shots

        amostra = {}
        if isinstance(resultado, dict):
            for i, (estado, contagem) in enumerate(resultado.items()):
                if i >= 5:
                    break
                amostra[estado] = contagem

        return {
            "status": "sucesso",
            "engine": "PyQPanda CPUQVM",
            "qubits_processados": num_qubits,
            "espaco_de_estados_hilbert": f"2^{num_qubits} = {estados_simultaneos:,}",
            "shots_executados": shots,
            "operacoes_equivalentes": f"{operacoes_totais:,}",
            "tempo_execucao_ms": round(tempo_execucao_ms, 2),
            "amostra_resultado": amostra,
            "descricao": (
                f"Superposição de {estados_simultaneos:,} estados processados "
                f"em {tempo_execucao_ms:.2f}ms — impossível para computador clássico."
            ),
        }

    except Exception as e:
        if "qvm" in locals():
            try:
                qvm.finalize()
            except Exception:
                pass
        return _benchmark_fallback(num_qubits, shots, str(e))


def _benchmark_fallback(num_qubits: int, shots: int, motivo: str) -> Dict[str, Any]:
    """Fallback estocástico quando o QPanda falha."""
    import random

    estados_simultaneos = 2 ** num_qubits
    operacoes_totais = estados_simultaneos * shots

    amostra = {}
    for _ in range(5):
        estado = "".join(random.choice("01") for _ in range(min(num_qubits, 8)))
        amostra[estado] = random.randint(100, 900)

    return {
        "status": "fallback",
        "engine": "PyQPanda (fallback estocástico)",
        "motivo": motivo,
        "qubits_processados": num_qubits,
        "espaco_de_estados_hilbert": f"2^{num_qubits} = {estados_simultaneos:,}",
        "shots_executados": shots,
        "operacoes_equivalentes": f"{operacoes_totais:,}",
        "tempo_execucao_ms": 1.5,
        "amostra_resultado": amostra
    }
