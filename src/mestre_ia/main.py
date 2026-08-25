import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Projeto Orion API",
    description="Backend para integração quântica PyQPanda e Android Atena",
    version="1.0.0"
)

class ChatPayload(BaseModel):
    prompt: str = Field("", description="Prompt do usuário")
    mensagem: str = Field("", description="Mensagem alternativa")

@app.get("/health")
def health_check():
    return {"status": "ok", "servico": "Projeto Orion API"}

@app.post("/quantum/benchmark")
def benchmark_qpanda(num_qubits: int = 14, shots: int = 1000):
    import time
    import pyqpanda as pq

    start_time = time.time()

    # Inicializa a Máquina Virtual Quântica em C++
    qvm = pq.CPUQVM()
    qvm.init_qvm()

    # Aloca os Qubits e Bits Clássicos
    qubits = qvm.qAlloc_many(num_qubits)
    cbits = qvm.cAlloc_many(num_qubits)

    prog = pq.QProg()
    
    # Coloca o primeiro Qubit em Superposição (Porta Hadamard)
    prog << pq.H(qubits[0])

    # Emaranha em cadeia todos os Qubits (Estado GHZ: |00...0> + |11...1>)
    for i in range(num_qubits - 1):
        prog << pq.CNOT(qubits[i], qubits[i+1])

    # Medição completa de todos os estados
    prog << pq.measure_all(qubits, cbits)
    resultado = qvm.run_with_configuration(prog, cbits, shots)

    tempo_execucao_ms = (time.time() - start_time) * 1000
    estados_simultaneos = 2 ** num_qubits
    operacoes_totais = estados_simultaneos * shots

    qvm.finalize()

    return {
        "status": "sucesso",
        "engine": "PyQPanda CPUQVM (C++ Kernel)",
        "qubits_processados": num_qubits,
        "espaco_de_estados_hilbert": f"2^{num_qubits} = {estados_simultaneos:,} estados simultâneos",
        "shots_executados": shots,
        "operacoes_equivalentes": f"{operacoes_totais:,}",
        "tempo_execucao_ms": round(tempo_execucao_ms, 2),
        "amostra_resultado_emaranhado": resultado
    }
