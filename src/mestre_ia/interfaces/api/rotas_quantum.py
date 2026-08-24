from fastapi import APIRouter, HTTPException, Depends
from mestre_ia.core.contratos import CircuitoQuantico
from mestre_ia.infraestrutura.adaptadores.quantum import QPandaAdapter
from mestre_ia.core.excecoes import ProvedorIndisponivelError, RespostaInesperadaError
from .schemas import RequisicaoCircuitoSchema, RespostaCircuitoSchema

router = APIRouter(prefix="/quantum", tags=["Computação Quântica"])

_adaptador_global = None

def obter_qpanda_adapter() -> QPandaAdapter:
    global _adaptador_global
    if _adaptador_global is None:
        _adaptador_global = QPandaAdapter()
    return _adaptador_global

@router.post("/simular", response_model=RespostaCircuitoSchema)
async def simular_circuito(
    requisicao: RequisicaoCircuitoSchema,
    adaptador: QPandaAdapter = Depends(obter_qpanda_adapter)
):
    try:
        circuito = CircuitoQuantico(
            num_qubits=requisicao.num_qubits,
            operacoes=[op.model_dump() for op in requisicao.operacoes],
            medicao=requisicao.medicao
        )

        resultado = await adaptador.executar_circuito(
            circuito=circuito,
            shots=requisicao.shots
        )

        return RespostaCircuitoSchema(
            status="sucesso",
            provedor=resultado.provedor.value if hasattr(resultado.provedor, 'value') else str(resultado.provedor),
            contagens=resultado.contagens,
            tempo_execucao_ms=resultado.tempo_execucao_ms
        )

    except ProvedorIndisponivelError as e:
        raise HTTPException(status_code=503, detail=f"Simulador indisponível: {str(e)}")
    except RespostaInesperadaError as e:
        raise HTTPException(status_code=400, detail=f"Erro na execução: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
