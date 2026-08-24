from pydantic import BaseModel
from typing import List, Dict, Optional

class OperacaoQuanticaSchema(BaseModel):
    gate: str
    target: int
    control: Optional[int] = None
    angle: Optional[float] = 0.0

class RequisicaoCircuitoSchema(BaseModel):
    num_qubits: int
    operacoes: List[OperacaoQuanticaSchema]
    medicao: List[int]
    shots: Optional[int] = 1024

class RespostaCircuitoSchema(BaseModel):
    status: str
    provedor: str
    contagens: Dict[str, int]
    tempo_execucao_ms: float
