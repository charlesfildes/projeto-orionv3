from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from mestre_ia.infraestrutura.adaptadores.quantum.qpanda_adapter import QPandaAdapter
from mestre_ia.dominio.servicos.orquestrador_servico import OrquestradorServico
from .rotas_quantum import obter_qpanda_adapter

router = APIRouter(prefix="/orquestrador", tags=["Orquestrador Orion"])

class RequisicaoOrquestradorSchema(BaseModel):
    prompt: str
    api_key_deepseek: Optional[str] = ""

@router.post("/executar")
async def executar_demanda(
    requisicao: RequisicaoOrquestradorSchema,
    qpanda: QPandaAdapter = Depends(obter_qpanda_adapter)
) -> Dict[str, Any]:
    servico = OrquestradorServico(qpanda_adapter=qpanda)
    return await servico.processar_requisicao(
        prompt=requisicao.prompt,
        api_key_deepseek=requisicao.api_key_deepseek
    )
