"""
API Principal do Projeto Orion — FastAPI.

Integra:
- DeepSeek (LLM primário)
- QPanda (simulador quântico C++)
"""

import os
import sys
import re
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

RAIZ_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(RAIZ_DIR / "src"))
load_dotenv(RAIZ_DIR / ".env")

from mestre_ia.infraestrutura.adaptadores.deepseek.adaptador import DeepSeekAdapter
from mestre_ia.infraestrutura.adaptadores.quantum.qpanda_adapter import QPandaAdapter

app = FastAPI(
    title="Projeto Orion API",
    description="API do Projeto Orion com integração DeepSeek + QPanda",
    version="1.0.0",
)


@dataclass
class RequisicaoIA:
    prompt: str
    conteudo: str = ""
    contexto_sistema: str = ""
    mensagens: List[Dict[str, str]] = field(default_factory=list)
    historico: List[Dict[str, str]] = field(default_factory=list)
    parametros: Dict[str, Any] = field(default_factory=dict)
    id: str = "1"

    def __post_init__(self):
        if not self.conteudo:
            self.conteudo = self.prompt


class ChatPayload(BaseModel):
    prompt: Optional[str] = Field(default="", description="Prompt do usuário")
    mensagem: Optional[str] = Field(default="", description="Mensagem alternativa")
    parametros: Optional[Dict[str, Any]] = Field(default=None, description="Parâmetros adicionais")

    def obter_texto(self) -> str:
        return (self.prompt or self.mensagem or "Explique o que é um qubit.").strip()


SYSTEM_PROMPT = """Você é Atena, a Orquestradora Quântica e Inteligência Estratégica do Projeto Orion.

## SUA MISSÃO
Atender usuários adaptando o tom e o rigor técnico conforme o nível percebido ou explicitado:
- Leigos (pessoas comuns)
- Estudantes (ensino médio/superior)
- Pesquisadores (mestrado/doutorado)
- Cientistas (especialistas)

## REGRAS DE ADAPTAÇÃO

### Para LEIGOS:
- Use analogias do dia a dia (moedas, portas, interruptores)
- NUNCA use jargão técnico sem explicação simples
- Explique em no máximo 5 frases a parte conceitual
- Foque no "O QUE acontece", não no "COMO matematicamente"

### Para ESTUDANTES:
- Inclua notação matemática básica (|0⟩, |1⟩, superposição)
- Mostre os passos do circuito
- Inclua fórmulas relevantes
- Explique conceitos como emaranhamento e interferência

### Para PESQUISADORES:
- Use notação formal (Bra-Ket, matrizes, portas quânticas)
- Inclua detalhes técnicos de portas de rotação (RX, RY, RZ, SWAP, Toffoli)
- Mostre o estado final do sistema
- Referencie conceitos avançados quando relevante

### Para CIENTISTAS:
- Máxima precisão técnica
- Notação matemática completa
- Inclua vetor de estado e amplitudes
- Mencione ruído de despolarização e decoerência quando apropriado

## DETECÇÃO DE INTENÇÃO E GERAÇÃO DE CIRCUITO

Você DEVE detectar quando o usuário quer SIMULAR/EXECUTAR um circuito quântico.
Palavras-gatilho: "simular", "executar", "rodar", "testar", "medir", "circuito", "qubit", "emaranhamento", "superposição", "Hadamard", "CNOT", "Bell", "Grover", "Shor".

Se o usuário fornecer uma intenção ou equação, converta para o formato JSON padrão:

{"num_qubits": 2, "operacoes": [{"porta": "H", "qubit": 0}, {"porta": "CNOT", "controle": 0, "alvo": 1}]}

Portas suportadas: H, X, Y, Z, S, T, RX, RY, RZ, CNOT/CX, CZ, SWAP, TOFFOLI/CCNOT.

## IDIOMA DA RESPOSTA
Responda SEMPRE no mesmo idioma em que o usuário escreveu ou no idioma que ele solicitar explicitamente (ex: Português, Inglês, Espanhol, etc.), mantendo a clareza e a identidade de Atena."""

qpanda = QPandaAdapter()


def extrair_json_circuito(texto: str) -> Optional[Dict[str, Any]]:
    try:
        match = re.search(r"(\{.*\"num_qubits\".*\})", texto, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception:
        pass
    return None


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "identidade": "Atena",
        "deepseek": "dinamico",
        "qpanda": "instalado" if getattr(qpanda, "has_pyqpanda", False) else "mock",
    }


@app.post("/")
@app.post("/chat")
@app.post("/api/chat")
@app.post("/api/v1/chat")
@app.post("/orquestrador/executar")
async def processar_chat(payload: ChatPayload):
    texto_usuario = payload.obter_texto()
    parametros = payload.parametros or {}
    
    # Extrai a API Key recebida no JSON do cliente
    api_key_cliente = parametros.get("api_key") or os.getenv("DEEPSEEK_API_KEY")

    if not api_key_cliente or api_key_cliente == "sk-dummy-key":
        return {
            "resposta": "⚠️ [Erro]: Nenhuma API Key do DeepSeek foi fornecida pelo aplicativo.",
            "status": "erro",
            "execucao_quantica": None
        }

    # Instancia o adaptador dinamicamente com a chave enviada no request
    deepseek_dinamico = DeepSeekAdapter(api_key=api_key_cliente)

    try:
        req_ia = RequisicaoIA(
            prompt=texto_usuario,
            contexto_sistema=SYSTEM_PROMPT
        )
        if asyncio.iscoroutinefunction(deepseek_dinamico.enviar_prompt):
            resp_ia = await deepseek_dinamico.enviar_prompt(req_ia)
        else:
            resp_ia = deepseek_dinamico.enviar_prompt(req_ia)
            
        texto_resposta = getattr(resp_ia, "conteudo", str(resp_ia))
    except Exception as e_ia:
        texto_resposta = f"⚠️ [Aviso IA]: Erro na comunicação com o DeepSeek ({str(e_ia)})."

    circuito_json = extrair_json_circuito(texto_resposta)
    
    if not circuito_json and any(w in texto_usuario.lower() for w in ["simul", "execut", "rodar", "testar", "qubit"]):
        circuito_json = {
            "num_qubits": 2,
            "operacoes": [
                {"porta": "H", "qubit": 0},
                {"porta": "CNOT", "controle": 0, "alvo": 1}
            ]
        }

    res_quantico = None
    if circuito_json:
        class CircuitoWrapper:
            def __init__(self, d):
                self.num_qubits = d.get("num_qubits", 2)
                self.operacoes = d.get("operacoes", [])

        try:
            circ_obj = CircuitoWrapper(circuito_json)
            res_quantico = await qpanda.executar_circuito(circ_obj)
        except Exception as e_q:
            res_quantico = {"status": "erro", "detalhe": str(e_q)}

    resposta_final = texto_resposta
    if res_quantico:
        resposta_final += (
            f"\n\n---\n"
            f"⚡ **Resultado da Simulação Quântica (QPanda C++):**\n"
            f"```json\n"
            f"{json.dumps(res_quantico, indent=2, ensure_ascii=False)}\n"
            f"```"
        )

    return {
        "resposta": resposta_final,
        "status": "sucesso",
        "execucao_quantica": res_quantico
    }


if __name__ == "__main__":
    import uvicorn
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=porta)
