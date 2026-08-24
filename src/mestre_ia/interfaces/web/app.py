import streamlit as st
import httpx

st.set_page_config(page_title="Projeto Orion - Chat", page_icon="🌌")
st.title("🌌 Projeto Orion — Chat Interativo")

# Inicializa o histórico de mensagens da sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Exibe as mensagens gravadas no histórico
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Entrada do usuário
prompt = st.chat_input("Digite sua mensagem...")

if prompt:
    # Exibe e salva mensagem do usuário
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Chamada ao backend FastAPI
    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            try:
                response = httpx.post(
                    "http://127.0.0.1:8000/orquestrador/executar",
                    json={"prompt": prompt},
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    dados = response.json()
                    
                    if dados.get("status") == "sucesso":
                        resposta_texto = dados.get("resposta")
                    else:
                        # Resposta do Fallback Quântico
                        resposta_texto = (
                            f"⚠️ **[Fallback Quântico Ativo]** {dados.get('motivo')}\n\n"
                            f"Entropia Gerada: `{dados.get('entropia_quantica')}`"
                        )
                else:
                    resposta_texto = f"Erro no servidor HTTP: {response.status_code}"
            except Exception as e:
                resposta_texto = f"Falha na comunicação com o backend FastAPI: {e}"

            st.write(resposta_texto)
            st.session_state.mensagens.append({"role": "assistant", "content": resposta_texto})
