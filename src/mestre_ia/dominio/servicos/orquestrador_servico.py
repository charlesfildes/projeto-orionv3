import os
import httpx
from typing import Dict, Any
from dotenv import load_dotenv
from mestre_ia.infraestrutura.adaptadores.quantum.qpanda_adapter import QPandaAdapter
from mestre_ia.core.contratos import CircuitoQuantico
from mestre_ia.core.logging_estruturado import obter_logger

load_dotenv()

logger = obter_logger("orion.orquestrador")

class OrquestradorServico:
    def __init__(self, qpanda_adapter: QPandaAdapter):
        self.qpanda_adapter = qpanda_adapter
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")

    async def processar_requisicao(self, prompt: str, api_key_deepseek: str = "") -> Dict[str, Any]:
        # Usa a chave enviada no JSON do curl ou cai no valor do .env
        chave_final = api_key_deepseek or self.deepseek_key

        try:
            if not chave_final or chave_final == "SUA_CHAVE_DEEPSEEK_AQUI":
                raise ValueError("Chave de API do DeepSeek ausente ou inválida.")

            logger.info("Conectando ao provedor primário (DeepSeek)...")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                resposta = await client.post(
                    self.deepseek_url,
                    headers={
                        "Authorization": f"Bearer {chave_final}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }
                )
                resposta.raise_for_status()
                dados = resposta.json()

                return {
                    "provedor_utilizado": "deepseek",
                    "status": "sucesso",
                    "resposta": dados["choices"][0]["message"]["content"]
                }

        except Exception as erro:
            logger.warning(f"Falha no provedor primário ({type(erro).__name__}). Ativando FALLBACK QUÂNTICO LOCAL!")
            return await self._executar_fallback_quantico(prompt)

    async def _executar_fallback_quantico(self, prompt: str) -> Dict[str, Any]:
        circuito_fallback = CircuitoQuantico(
            num_qubits=2,
            operacoes=[
                {"gate": "H", "target": 0},
                {"gate": "H", "target": 1}
            ],
            medicao=[0, 1]
        )

        resultado = await self.qpanda_adapter.executar_circuito(circuito_fallback, shots=100)
        
        provedor_str = (
            resultado.provedor.value 
            if hasattr(resultado.provedor, 'value') 
            else str(resultado.provedor)
        )

        return {
            "provedor_utilizado": f"{provedor_str}_fallback",
            "status": "fallback_ativo",
            "motivo": "Falha na comunicação com a API do DeepSeek.",
            "entropia_quantica": resultado.contagens,
            "mensagem": f"Processado via fallback quântico local para o prompt: '{prompt}'"
        }
