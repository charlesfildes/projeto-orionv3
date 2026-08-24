import os
import sys
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Configuração do caminho de importação e ambiente
RAIZ_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(RAIZ_DIR / "src"))
load_dotenv(RAIZ_DIR / ".env")

from mestre_ia.infraestrutura.adaptadores.deepseek.adaptador import DeepSeekAdapter
from mestre_ia.infraestrutura.adaptadores.quantum.qpanda_adapter import QPandaAdapter

app = FastAPI(title="Projeto Orion API")

class ChatPayload(BaseModel):
    prompt: Optional[str] = ""
    mensagem: Optional[str] = ""
    parametros: Optional[Dict[str, Any]] = None

@dataclass
class RequisicaoDTO:
    prompt: str
    conteudo: str = ""
    
    def __post_init__(self):
        if not self.conteudo:
            self.conteudo = self.prompt

@dataclass
class CircuitoDTO:
    num_qubits: int = 2
    operacoes: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"porta": "H", "qubit": 0},
        {"porta": "CNOT", "controle": 0, "alvo": 1}
    ])

# Instanciação defensiva dos adaptadores
api_key = os.getenv("DEEPSEEK_API_KEY") or "sk-dummy-key"
deepseek = DeepSeekAdapter(api_key=api_key)
qpanda = QPandaAdapter()

@app.post("/")
@app.post("/chat")
@app.post("/api/chat")
@app.post("/api/v1/chat")
@app.post("/orquestrador/executar")
async def processar_chat(payload: ChatPayload):
    try:
        texto_usuario = payload.prompt or payload.mensagem or "Consulta padrão quântica"
        
        # 1. Formulação Teórica via DeepSeek
        req = RequisicaoDTO(prompt=texto_usuario)
        if asyncio.iscoroutinefunction(deepseek.enviar_prompt):
            resp_ia = await deepseek.enviar_prompt(req)
        else:
            resp_ia = deepseek.enviar_prompt(req)

        texto_resposta = getattr(resp_ia, "conteudo", str(resp_ia))

        # 2. Execução do Circuito no Simulador C++ (QPanda)
        circuito = CircuitoDTO(num_qubits=2)
        if asyncio.iscoroutinefunction(qpanda.executar_circuito):
            res_quantico = await qpanda.executar_circuito(circuito)
        else:
            res_quantico = qpanda.executar_circuito(circuito)

        # 3. Consolidação no formato final exibido no chat
        resposta_formatada = (
            f"{texto_resposta}\n\n"
            f"---\n"
            f"⚡ **Resultado da Simulação Quântica (QPanda C++):**\n"
            f"```json\n"
            f"Provedor: {res_quantico.get('provedor', 'origin_quantum_qpanda')}\n"
            f"Distribuição de Estados: {res_quantico.get('entropia_quantica', {})}\n"
            f"```"
        )

        return {
            "resposta": resposta_formatada,
            "status": "sucesso",
            "execucao_quantica": res_quantico
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
