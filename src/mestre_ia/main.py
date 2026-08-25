import os
import sys
import json
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
    return {"status": "ok", "servico": "Projeto Orion API", "deepseek_key_configurada": bool(DEEPSEEK_API_KEY)}

@app.post("/orquestrador/executar")
async def orquestrar_resposta(payload: ChatPayload):
    import httpx
    texto_usuario = payload.prompt or payload.mensagem
    if not texto_usuario:
        raise HTTPException(status_code=400, detail="Prompt não informado.")

    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY não configurada no ambiente do Cloud Run.")

    # 1. DeepSeek Traduz Linguagem Natural para Parâmetros Quânticos
    prompt_traducao = f"""
    Você é o orquestrador do Projeto Orion.
    Analise o pedido do usuário e determine quantos qubits (1 a 10) e shots (100 a 1000) devem ser simulados.
    Responda EXCLUSIVAMENTE em formato json com a estrutura: {{"qubits": 3, "shots": 1000}}
    
    Pedido do usuário: {texto_usuario}
    """

    try:
        async with httpx.AsyncClient() as client:
            res1 = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt_traducao}],
                    "response_format": {"type": "json_object"}
                },
                timeout=25.0
            )
            if res1.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Erro DeepSeek Etapa 1 ({res1.status_code}): {res1.text}")
            
            config_quantica = json.loads(res1.json()["choices"][0]["message"]["content"])
            num_qubits = min(max(int(config_quantica.get("qubits", 3)), 1), 10)
            shots = min(max(int(config_quantica.get("shots", 1000)), 100), 1000)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha de conexão com DeepSeek Etapa 1: {str(e)}")

    # 2. Execução da Simulação no Engine PyQPanda
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
            prog << pq.CNOT(qubits[i], qubits[i+1])

        prog << pq.measure_all(qubits, cbits)
        resultado_bruto = qvm.run_with_configuration(prog, cbits, shots)
        qvm.finalize()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na execução quântica PyQPanda: {str(e)}")

    # 3. DeepSeek Traduz os Resultados Numéricos para Linguagem Simples
    prompt_explicacao = f"""
    Você é o assistente quântico do app Atena.
    O usuário perguntou: "{texto_usuario}"
    
    A simulação do PyQPanda gerou este resultado bruto de medição estatística:
    {json.dumps(resultado_bruto)}
    
    Explique esse resultado de forma didática, simples e acessível em português para o usuário.
    """

    try:
        async with httpx.AsyncClient() as client:
            res2 = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt_explicacao}]
                },
                timeout=25.0
            )
            if res2.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Erro DeepSeek Etapa 3 ({res2.status_code}): {res2.text}")
                
            resposta_final = res2.json()["choices"][0]["message"]["content"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha de conexão com DeepSeek Etapa 3: {str(e)}")

    return {
        "status": "sucesso",
        "resposta_orion": resposta_final,
        "dados_tecnicos_internos": {
            "qubits_utilizados": num_qubits,
            "shots": shots,
            "resultado_pyqpanda": resultado_bruto
        }
    }
