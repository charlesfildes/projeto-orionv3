import sys
from pathlib import Path
import os
import asyncio
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Mapeia a pasta src no sys.path
RAIZ_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ_DIR / "src"))

load_dotenv()

from mestre_ia.infraestrutura.adaptadores.deepseek.adaptador import DeepSeekAdapter
from mestre_ia.infraestrutura.adaptadores.quantum.qpanda_adapter import QPandaAdapter


# Objeto Mock resiliente para a requisição da IA
@dataclass
class RequisicaoMock:
    prompt: str
    conteudo: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    contexto_sistema: str = "Você é um assistente especializado em computação quântica."
    historico: List[dict] = field(default_factory=list)
    parametros: Dict[str, Any] = field(default_factory=dict)
    modelo: Optional[str] = None

    def __post_init__(self):
        if not self.conteudo:
            self.conteudo = self.prompt

    def __getattr__(self, name: str) -> Any:
        return None


# Objeto Mock para o Circuito Quântico contendo num_qubits e atributos esperados
@dataclass
class CircuitoMock:
    num_qubits: int = 2
    operacoes: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"porta": "H", "qubit": 0},
        {"porta": "CNOT", "controle": 0, "alvo": 1}
    ])

    def __getattr__(self, name: str) -> Any:
        return None


async def testar_fluxo_conjugado():
    print("🌌 [1/3] Enviando problema quântico para o DeepSeek...")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    deepseek = DeepSeekAdapter(api_key=api_key)
    qpanda = QPandaAdapter()

    prompt_texto = (
        "Formule um circuito quântico de Bell (Hadamard + CNOT) "
        "para medir 2 qubits e explique o colapso dos estados."
    )

    try:
        # Step 1: Chamada ao DeepSeek
        requisicao = RequisicaoMock(
            prompt=prompt_texto, 
            conteudo=prompt_texto,
            parametros={"temperature": 0.7}
        )

        if asyncio.iscoroutinefunction(deepseek.enviar_prompt):
            resposta = await deepseek.enviar_prompt(requisicao)
        else:
            resposta = deepseek.enviar_prompt(requisicao)
        
        texto_resposta = getattr(resposta, "conteudo", str(resposta))
        print(f"\n🤖 Resposta da IA (DeepSeek):\n{texto_resposta}\n")

        # Step 2: Execução no QPanda C++ via DTO
        print("⚡ [2/3] Executando simulação de estados no QPanda (C++)...")
        
        circuito_bell = CircuitoMock(num_qubits=2)

        if asyncio.iscoroutinefunction(qpanda.executar_circuito):
            resultado_quantico = await qpanda.executar_circuito(circuito_bell)
        else:
            resultado_quantico = qpanda.executar_circuito(circuito_bell)

        print("\n📊 [3/3] Resultado do Processamento Quântico Local (QPanda):")
        print(f"Resultado da Simulação: {resultado_quantico}")

    except Exception as e:
        print(f"❌ Erro no teste: {e}")


if __name__ == "__main__":
    asyncio.run(testar_fluxo_conjugado())
