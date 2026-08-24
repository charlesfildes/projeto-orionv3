import asyncio
from mestre_ia.infraestrutura.adaptadores.quantum import QPandaAdapter
from mestre_ia.core.contratos import CircuitoQuantico

async def executar_algoritmo_orion():
    adaptador = QPandaAdapter()
    
    # Define as portas e alocações do circuito
    circuito = CircuitoQuantico(
        num_qubits=2,
        operacoes=[
            {'gate': 'H', 'target': 0},
            {'gate': 'CNOT', 'control': 0, 'target': 1},
        ],
        medicao=[0, 1],
    )
    
    # Submete ao CPUQVM local
    resultado = await adaptador.executar_circuito(circuito, shots=1024)
    return resultado.contagens

# Executa o loop assíncrono do Orion
contagens = asyncio.run(executar_algoritmo_orion())
print("Histograma final:", contagens)
