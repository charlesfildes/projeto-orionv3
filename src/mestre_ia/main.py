import os
import sys
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Projeto Orion API",
    description="Orquestrador Quântico: DeepSeek + PyQPanda",
    version="1.0.0"
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

class ChatPayload(BaseModel):
    prompt: str = Field("", description="Prompt do usuário em linguagem natural")
    mensagem: str = Field("", description="Mensagem alternativa")

@app.get("/health")
def health_check():
    return {"status": "ok", "servico": "Projeto Orion API"}

@app.post("/orquestrador/executar")
async def orquestrar_resposta(payload: ChatPayload):
    texto_usuario = payload.prompt or payload.mensagem
    if not texto_usuario:
        raise HTTPException(status_code=400, detail="Prompt não informado.")

    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY não configurada no servidor.")

    # 1. DeepSeek Traduz Linguagem Natural para Parâmetros do Circuito Quântico
    prompt_traducao = f"""
    Você é o orquestrador do Projeto Orion.
    Analise o pedido do usuário e determine quantos qubits (1 a 10) e shots (100 a 1000) devem ser simulados.
    Responda EXCLUSIVAMENTE um JSON no formato: {{"qubits": 2, "shots": 1000, "explicacao_tecnica": "motivo"}}
    
    Pedido do usuário: {texto_usuario}
    """

    async with httpx.AsyncClient() as client:
        res1 = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt_traducao}],
                "response_format": {"type": "json_object"}
            },
            timeout=30.0
        )
        
        if res1.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro na API DeepSeek: {res1.text}")

        config_quantica = json.loads(res1.json()["choices"][0]["message"]["content"])
        num_qubits = min(max(config_quantica.get("qubits", 2), 1), 10)
        shots = min(max(config_quantica.get("shots", 1000), 100), 1000)

    # 2. Execução da Simulação no Engine PyQPanda
    import pyqpanda as pq
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
    resultado_bruto = qvm.run_with_configuration(prog, cbits, shots)
    qvm.finalize()

    # 3. DeepSeek Traduz os Resultados Numéricos para Linguagem Simples
    prompt_explicacao = f"""
    Você é o assistente quântico do app Atena.
    O usuário perguntou: "{texto_usuario}"
    
    A simulação do PyQPanda gerou este resultado bruto de medição estatística:
    {json.dumps(resultado_bruto)}
    
    Explique esse resultado de forma didática, simples e acessível em português para o usuário.
    """

    async with httpx.AsyncClient() as client:
        res2 = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt_explicacao}]
            },
            timeout=30.0
        )
        
        resposta_final = res2.json()["choices"][0]["message"]["content"]

    return {
        "status": "sucesso",
        "resposta_orion": resposta_final,
        "dados_tecnicos_internos": {
            "qubits_utilizados": num_qubits,
            "shots": shots,
            "resultado_pyqpanda": resultado_bruto
        }
    }
