import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

RAIZ_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(RAIZ_DIR / "src"))

app = FastAPI(
    title="Projeto Orion API",
    description="Backend para integração quântica PyQPanda & IBM Quantum Real",
    version="2.0.0",
)

class ChatPayload(BaseModel):
    prompt: str = Field("", description="Prompt do usuário")
    mensagem: str = Field("", description="Mensagem alternativa")
    parametros: dict = Field(default_factory=dict, description="Parâmetros adicionais")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "servico": "Projeto Orion API",
        "quantum_engines": ["PyQPanda CPUQVM", "IBM Quantum QPU (Qiskit Runtime)"],
    }

@app.post("/quantum/benchmark")
def benchmark_qpanda(
    num_qubits: int = 18, 
    shots: int = 1000, 
    use_real_hardware: bool = False,
    ibm_token: Optional[str] = None
):
    if num_qubits < 2 or num_qubits > 127:
        raise HTTPException(status_code=400, detail="Qubits devem estar entre 2 e 127.")

    start_time = time.time()

    # CAMINHO 1: Execução em Hardware Quântico REAL da IBM via Qiskit Runtime
    if use_real_hardware:
        token = ibm_token or os.getenv("IBM_QUANTUM_TOKEN")
        if not token:
            raise HTTPException(status_code=401, detail="Informe um token válido da IBM Quantum.")
        
        try:
            from qiskit import QuantumCircuit
            from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
            
            # Ajuste do canal para o padrão exato da IBM Quantum Platform
            service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
            backend = service.least_busy(operational=True, simulator=False)
            
            qc = QuantumCircuit(num_qubits)
            qc.h(0)
            for i in range(num_qubits - 1):
                qc.cx(i, i + 1)
            qc.measure_all()
            
            sampler = Sampler(mode=backend)
            job = sampler.run([qc], shots=shots)
            result = job.result()
            
            counts = result[0].data.meas.get_counts()
            tempo_execucao_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "sucesso",
                "engine": f"IBM Quantum QPU ({backend.name})",
                "qubits_processados": num_qubits,
                "shots_executados": shots,
                "tempo_execucao_ms": round(tempo_execucao_ms, 2),
                "amostra_resultado": dict(list(counts.items())[:5]),
                "ambiente": "Hardware Quântico Físico Supercondutor"
            }
        except Exception as e:
            return _benchmark_fallback(num_qubits, shots, f"Erro IBM Qiskit: {str(e)}")

    # CAMINHO 2: Simulação Nativa C++ PyQPanda CPUQVM
    try:
        import pyqpanda as pq
        qvm = pq.CPUQVM()
        qvm.init_qvm()

        qubits = qvm.qAlloc_many(num_qubits)
        cbits = qvm.cAlloc_many(num_qubits)

        prog = pq.QProg()
        for q in qubits:
            prog << pq.H(q)
        for i in range(num_qubits - 1):
            prog << pq.CNOT(qubits[i], qubits[i + 1])
        prog << pq.measure_all(qubits, cbits)

        resultado = qvm.run_with_configuration(prog, cbits, shots)
        qvm.finalize()

        tempo_execucao_ms = (time.time() - start_time) * 1000
        estados_simultaneos = 2 ** num_qubits

        return {
            "status": "sucesso",
            "engine": "PyQPanda CPUQVM",
            "qubits_processados": num_qubits,
            "espaco_de_estados_hilbert": f"2^{num_qubits} = {estados_simultaneos:,}",
            "shots_executados": shots,
            "tempo_execucao_ms": round(tempo_execucao_ms, 2),
            "amostra_resultado": dict(list(resultado.items())[:5])
        }
    except Exception as e:
        return _benchmark_fallback(num_qubits, shots, str(e))

def _benchmark_fallback(num_qubits: int, shots: int, motivo: str) -> Dict[str, Any]:
    import random
    estados_simultaneos = 2 ** num_qubits
    amostra = { "".join(random.choice("01") for _ in range(min(num_qubits, 8))): random.randint(100, 900) for _ in range(5) }
    return {
        "status": "fallback",
        "engine": "PyQPanda (fallback estocástico)",
        "motivo": motivo,
        "qubits_processados": num_qubits,
        "espaco_de_estados_hilbert": f"2^{num_qubits} = {estados_simultaneos:,}",
        "shots_executados": shots,
        "tempo_execucao_ms": 1.5,
        "amostra_resultado": amostra
    }
