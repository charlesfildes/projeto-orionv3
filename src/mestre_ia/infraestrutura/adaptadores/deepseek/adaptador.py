"""
DeepSeekAdapter — Implementação do contrato IAProviderPort para DeepSeek.

Versão do contrato: 1.0
API: https://api.deepseek.com/chat/completions
Documentação: https://platform.deepseek.com/api-docs
"""

import json
import time
from typing import AsyncIterator, List, Optional

import httpx

from mestre_ia.core.contratos import (
    IAProviderPort,
    RequisicaoIA,
    RespostaIA,
    TipoProvedorIA,
)
from mestre_ia.core.capacidades import (
    DominioTarefa,
    PerfilCapacidade,
    RegistroCapacidades,
)
from mestre_ia.core.excecoes import (
    LimiteExcedidoError,
    ProvedorIndisponivelError,
    RespostaInesperadaError,
    TimeoutExcedidoError,
    TokenInvalidoError,
    ConfiguracaoInvalidaError,
)
from mestre_ia.core.logging_estruturado import obter_logger, LoggerComContexto

logger = LoggerComContexto(obter_logger("deepseek.adaptador"))


class DeepSeekAdapter:
    """
    Adaptador para API do DeepSeek.

    Implementa IAProviderPort v1.0.
    Comunica-se com a API oficial via httpx assíncrono.
    """

    VERSAO_CONTRATO: str = "1.0"

    _URL_API: str = "https://api.deepseek.com/chat/completions"

    _CAPACIDADES_PADRAO: dict = {
        DominioTarefa.CONVERSACAO: 0.9,
        DominioTarefa.RACIOCINIO_LOGICO: 0.8,
        DominioTarefa.MATEMATICA: 0.8,
        DominioTarefa.PROGRAMACAO: 0.9,
        DominioTarefa.MEDICINA: 0.7,
        DominioTarefa.CIENCIAS: 0.8,
        DominioTarefa.PESQUISA: 0.7,
        DominioTarefa.DADOS: 0.8,
    }

    def __init__(
        self,
        api_key: str,
        modelo_padrao: str = "deepseek-chat",
        registro_capacidades: Optional[RegistroCapacidades] = None,
        timeout_ms: int = 30000,
    ):
        if not api_key or not api_key.strip():
            raise ConfiguracaoInvalidaError(
                chave="DEEPSEEK_API_KEY",
                valor="<vazia>",
                esperado="Chave de API válida (começa com sk-)"
            )
        if not modelo_padrao or not modelo_padrao.strip():
            raise ConfiguracaoInvalidaError(
                chave="DEEPSEEK_MODELO_PADRAO",
                valor="<vazio>",
                esperado="Nome do modelo (ex: deepseek-chat)"
            )
        if timeout_ms <= 0:
            raise ConfiguracaoInvalidaError(
                chave="timeout_ms",
                valor=str(timeout_ms),
                esperado="Valor maior que zero"
            )

        self._api_key = api_key.strip()
        self._modelo_padrao = modelo_padrao.strip()
        self._timeout_ms = timeout_ms

        if registro_capacidades is not None:
            perfil = PerfilCapacidade(
                modelo=self._modelo_padrao,
                provedor="deepseek",
                scores=dict(self._CAPACIDADES_PADRAO),
                suporta_streaming=True,
            )
            registro_capacidades.registrar(perfil)
            logger.debug(
                "Capacidades registradas",
                modelo=self._modelo_padrao,
                provedor="deepseek"
            )

    @property
    def provedor(self) -> TipoProvedorIA:
        return TipoProvedorIA.DEEPSEEK

    @property
    def modelos_disponiveis(self) -> List[str]:
        return ["deepseek-chat", "deepseek-coder"]

    async def enviar_prompt(
        self,
        requisicao: RequisicaoIA,
        timeout_ms: int = 30000
    ) -> RespostaIA:
        inicio = time.monotonic()
        timeout = timeout_ms if timeout_ms > 0 else self._timeout_ms
        timeout_segundos = timeout / 1000.0

        payload = self._construir_payload(requisicao)
        headers = self._construir_headers()

        logger.debug(
            "Enviando requisição para DeepSeek",
            modelo=payload.get("model"),
            timeout_ms=timeout,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout_segundos) as client:
                resposta_http = await client.post(
                    self._URL_API,
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException:
            logger.warning(
                "Timeout na requisição ao DeepSeek",
                timeout_ms=timeout,
                modelo=payload.get("model"),
            )
            raise TimeoutExcedidoError(
                provedor="deepseek",
                timeout_ms=timeout,
            )
        except httpx.ConnectError as e:
            logger.error(
                "Erro de conexão com DeepSeek",
                erro=str(e),
            )
            raise ProvedorIndisponivelError(
                provedor="deepseek",
                tentativa=1,
            )

        self._verificar_erro_http(resposta_http)
        dados = resposta_http.json()

        self._validar_resposta_api(dados)

        conteudo = dados["choices"][0]["message"]["content"]
        modelo_usado = dados.get("model", self._modelo_padrao)
        uso = dados.get("usage", {})
        tokens_entrada = uso.get("prompt_tokens", 0)
        tokens_saida = uso.get("completion_tokens", 0)

        tempo_decorrido = (time.monotonic() - inicio) * 1000.0

        logger.info(
            "Resposta recebida do DeepSeek",
            modelo=modelo_usado,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
            tempo_ms=round(tempo_decorrido, 2),
        )

        return RespostaIA(
            conteudo=conteudo,
            provedor=TipoProvedorIA.DEEPSEEK,
            modelo=modelo_usado,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
            tempo_resposta_ms=tempo_decorrido,
            requisicao_id=requisicao.id,
        )

    async def enviar_prompt_streaming(
        self,
        requisicao: RequisicaoIA,
        timeout_ms: int = 60000
    ) -> AsyncIterator[str]:
        timeout = timeout_ms if timeout_ms > 0 else self._timeout_ms
        timeout_segundos = timeout / 1000.0

        payload = self._construir_payload(requisicao)
        payload["stream"] = True
        headers = self._construir_headers()

        logger.debug(
            "Iniciando streaming DeepSeek",
            modelo=payload.get("model"),
        )

        try:
            async with httpx.AsyncClient(timeout=timeout_segundos) as client:
                async with client.stream(
                    "POST",
                    self._URL_API,
                    json=payload,
                    headers=headers,
                ) as resposta_http:
                    self._verificar_erro_http(resposta_http)

                    async for linha in resposta_http.aiter_lines():
                        if not linha or linha.startswith(":"):
                            continue
                        if linha.strip() == "[DONE]":
                            logger.debug("Streaming concluído [DONE]")
                            break
                        if linha.startswith("data: "):
                            dados_str = linha[6:]
                            try:
                                dados = json.loads(dados_str)
                                delta = dados.get("choices", [{}])[0].get("delta", {})
                                conteudo = delta.get("content", "")
                                if conteudo:
                                    yield conteudo
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue

        except httpx.TimeoutException:
            raise TimeoutExcedidoError(provedor="deepseek", timeout_ms=timeout)
        except httpx.ConnectError:
            raise ProvedorIndisponivelError(provedor="deepseek", tentativa=1)

    def _construir_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _construir_payload(self, requisicao: RequisicaoIA) -> dict:
        mensagens = []

        if requisicao.contexto_sistema:
            mensagens.append({
                "role": "system",
                "content": requisicao.contexto_sistema
            })

        for msg in requisicao.historico:
            mensagens.append(msg)

        mensagens.append({
            "role": "user",
            "content": requisicao.prompt
        })

        payload = {
            "model": requisicao.parametros.get("modelo", self._modelo_padrao),
            "messages": mensagens,
            "stream": False,
        }

        for param in ("temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"):
            if param in requisicao.parametros:
                payload[param] = requisicao.parametros[param]

        return payload

    def _verificar_erro_http(self, resposta: httpx.Response) -> None:
        if resposta.status_code == 401:
            raise TokenInvalidoError(provedor="deepseek")
        elif resposta.status_code == 429:
            raise LimiteExcedidoError(provedor="deepseek")
        elif resposta.status_code >= 500:
            raise ProvedorIndisponivelError(provedor="deepseek")
        elif resposta.status_code >= 400:
            raise RespostaInesperadaError(
                provedor="deepseek",
                detalhe=f"HTTP {resposta.status_code}",
                resposta_bruta=resposta.text[:200]
            )

    def _validar_resposta_api(self, dados: dict) -> None:
        if not isinstance(dados, dict):
            raise RespostaInesperadaError(
                provedor="deepseek",
                detalhe="Resposta não é um objeto JSON válido",
                resposta_bruta=str(dados)[:200]
            )
        if "choices" not in dados:
            raise RespostaInesperadaError(
                provedor="deepseek",
                detalhe="Resposta sem campo 'choices'",
                resposta_bruta=str(dados)[:200]
            )
        if not dados["choices"]:
            raise RespostaInesperadaError(
                provedor="deepseek",
                detalhe="Lista 'choices' está vazia",
                resposta_bruta=str(dados)[:200]
            )
        choice = dados["choices"][0]
        if "message" not in choice:
            raise RespostaInesperadaError(
                provedor="deepseek",
                detalhe="Choice sem campo 'message'",
                resposta_bruta=str(choice)[:200]
            )
        if "content" not in choice["message"]:
            raise RespostaInesperadaError(
                provedor="deepseek",
                detalhe="Message sem campo 'content'",
                resposta_bruta=str(choice["message"])[:200]
            )