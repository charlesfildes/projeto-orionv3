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
    parametros: dict = Field(default_factory=dict, description="Parâmetros adicionais")

@app.get("/health")
def health_check():
    return {"status": "ok", "servico": "Projeto Orion API"}

@app.post("/")
@app.post("/chat")
@app.post("/api/chat")
@app.post("/api/v1/chat")
@app.post("/orquestrador/executar")
def processar_chat(payload: ChatPayload):
    texto = payload.prompt or payload.mensagem or "Sem mensagem"
    return {"status": "sucesso", "resposta": f"Orion recebeu: {texto}"}

@app.post("/quantum/benchmark")
def benchmark_qpanda(num_qubits: int = 18, shots: int = 1000):
    import time
    import pyqpanda as pq

    start_time = time.time()

    qvm = pq.CPUQVM()
    qvm.init_qvm()

    qubits = qvm.qAlloc_many(num_qubits)
    cbits = qvm.cAlloc_many(num_qubits)

    prog = pq.QProg()
    for q in qubits:
        prog << pq.H(q)

    for i in range(num_qubits - 1):
        prog << pq.CNOT(qubits[i], qubits[i+1])

    prog << pq.measure_all(qubits, cbits)
    resultado = qvm.run_with_configuration(prog, cbits, shots)

    tempo_execucao_ms = (time.time() - start_time) * 1000
    estados_simultaneos = 2 ** num_qubits
    operacoes_totais = estados_simultaneos * shots

    qvm.finalize()

    return {
        "status": "sucesso",
        "engine": "PyQPanda CPUQVM",
        "qubits_processados": num_qubits,
        "espaco_de_estados_hilbert": f"2^{num_qubits} = {estados_simultaneos:,} estados simultaneos",
        "shots_executados": shots,
        "operacoes_equivalentes": f"{operacoes_totais:,}",
        "tempo_execucao_ms": round(tempo_execucao_ms, 2),
        "amostra_resultado": dict(list(resultado.items())[:5])
    }
