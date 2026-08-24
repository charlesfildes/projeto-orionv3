"""
Testes unitários para DeepSeekAdapter.

Utiliza mocks de httpx — sem chamadas reais à API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from mestre_ia.infraestrutura.adaptadores.deepseek import DeepSeekAdapter
from mestre_ia.core.contratos import (
    RequisicaoIA,
    RespostaIA,
    TipoProvedorIA,
)
from mestre_ia.core.capacidades import (
    DominioTarefa,
    RegistroCapacidades,
)
from mestre_ia.core.excecoes import (
    ConfiguracaoInvalidaError,
    LimiteExcedidoError,
    ProvedorIndisponivelError,
    RespostaInesperadaError,
    TimeoutExcedidoError,
    TokenInvalidoError,
)


@pytest.fixture
def adaptador():
    """Cria um adaptador básico para testes."""
    return DeepSeekAdapter(
        api_key="sk-teste-123",
        modelo_padrao="deepseek-chat",
    )


@pytest.fixture
def adaptador_com_registro():
    """Cria adaptador com registro de capacidades."""
    registro = RegistroCapacidades()
    adaptador = DeepSeekAdapter(
        api_key="sk-teste-456",
        modelo_padrao="deepseek-chat",
        registro_capacidades=registro,
    )
    return adaptador, registro


@pytest.fixture
def requisicao_basica():
    """Requisição básica para testes."""
    return RequisicaoIA(prompt="Qual e a capital do Brasil?")


@pytest.fixture
def requisicao_com_contexto():
    """Requisição com contexto de sistema."""
    return RequisicaoIA(
        prompt="Explique hipertensao",
        contexto_sistema="Voce e um medico especialista.",
    )


@pytest.fixture
def resposta_api_sucesso():
    """Mock de resposta de sucesso da API DeepSeek."""
    return {
        "id": "resp-123",
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "A capital do Brasil e Brasilia."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        }
    }


class TestInicializacao:
    """Testes de inicialização do adaptador."""

    def test_inicializacao_valida(self):
        """Deve criar adaptador com parâmetros válidos."""
        adaptador = DeepSeekAdapter(
            api_key="sk-teste",
            modelo_padrao="deepseek-chat",
            timeout_ms=30000,
        )
        assert adaptador.provedor == TipoProvedorIA.DEEPSEEK
        assert "deepseek-chat" in adaptador.modelos_disponiveis

    def test_api_key_vazia_lanca_erro(self):
        """Deve rejeitar API key vazia."""
        with pytest.raises(ConfiguracaoInvalidaError):
            DeepSeekAdapter(api_key="", modelo_padrao="deepseek-chat")

    def test_api_key_apenas_espacos_lanca_erro(self):
        """Deve rejeitar API key com apenas espaços."""
        with pytest.raises(ConfiguracaoInvalidaError):
            DeepSeekAdapter(api_key="   ", modelo_padrao="deepseek-chat")

    def test_modelo_vazio_lanca_erro(self):
        """Deve rejeitar modelo vazio."""
        with pytest.raises(ConfiguracaoInvalidaError):
            DeepSeekAdapter(api_key="sk-teste", modelo_padrao="")

    def test_timeout_zero_ou_negativo_lanca_erro(self):
        """Deve rejeitar timeout <= 0."""
        with pytest.raises(ConfiguracaoInvalidaError):
            DeepSeekAdapter(api_key="sk-teste", timeout_ms=0)
        with pytest.raises(ConfiguracaoInvalidaError):
            DeepSeekAdapter(api_key="sk-teste", timeout_ms=-100)

    def test_propriedade_provedor(self, adaptador):
        """propriedade provedor deve retornar DEEPSEEK."""
        assert adaptador.provedor == TipoProvedorIA.DEEPSEEK

    def test_modelos_disponiveis(self, adaptador):
        """Deve retornar lista de modelos."""
        modelos = adaptador.modelos_disponiveis
        assert "deepseek-chat" in modelos
        assert "deepseek-coder" in modelos

    def test_registro_capacidades(self, adaptador_com_registro):
        """Deve registrar capacidades quando registro é fornecido."""
        _, registro = adaptador_com_registro
        perfil = registro.obter_perfil("deepseek-chat")
        assert perfil is not None
        assert perfil.suporta(DominioTarefa.MEDICINA)

    def test_sem_registro_capacidades(self):
        """Deve funcionar sem registro de capacidades."""
        adaptador = DeepSeekAdapter(api_key="sk-teste")
        assert adaptador.provedor == TipoProvedorIA.DEEPSEEK


class TestConstrucaoPayload:
    """Testes de conversão RequisicaoIA -> payload HTTP."""

    def test_payload_basico(self, adaptador, requisicao_basica):
        """Deve construir payload com mensagem user."""
        payload = adaptador._construir_payload(requisicao_basica)
        assert payload["model"] == "deepseek-chat"
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert "capital do Brasil" in payload["messages"][0]["content"]

    def test_payload_com_contexto_sistema(self, adaptador, requisicao_com_contexto):
        """Deve incluir mensagem system quando contexto_sistema existe."""
        payload = adaptador._construir_payload(requisicao_com_contexto)
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"

    def test_payload_respeita_modelo_da_requisicao(self, adaptador):
        """Deve usar modelo da requisição se especificado."""
        req = RequisicaoIA(prompt="Teste", parametros={"modelo": "deepseek-coder"})
        payload = adaptador._construir_payload(req)
        assert payload["model"] == "deepseek-coder"

    def test_payload_com_parametros_adicionais(self, adaptador):
        """Deve incluir temperature e max_tokens quando fornecidos."""
        req = RequisicaoIA(
            prompt="Teste",
            parametros={"temperature": 0.7, "max_tokens": 100}
        )
        payload = adaptador._construir_payload(req)
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 100


class TestEnviarPromptSucesso:
    """Testes de envio de prompt com resposta bem-sucedida."""

    @pytest.mark.asyncio
    async def test_resposta_sucesso(self, adaptador, requisicao_basica, resposta_api_sucesso):
        """Deve retornar RespostaIA em caso de sucesso."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = resposta_api_sucesso

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            resposta = await adaptador.enviar_prompt(requisicao_basica)

        assert isinstance(resposta, RespostaIA)
        assert resposta.conteudo == "A capital do Brasil e Brasilia."
        assert resposta.provedor == TipoProvedorIA.DEEPSEEK
        assert resposta.modelo == "deepseek-chat"
        assert resposta.tokens_entrada == 10
        assert resposta.tokens_saida == 8
        assert resposta.requisicao_id == requisicao_basica.id

    @pytest.mark.asyncio
    async def test_resposta_propaga_requisicao_id(self, adaptador, requisicao_basica, resposta_api_sucesso):
        """Deve propagar requisicao_id para RespostaIA."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = resposta_api_sucesso

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            resposta = await adaptador.enviar_prompt(requisicao_basica)

        assert resposta.requisicao_id == requisicao_basica.id


class TestErrosHTTP:
    """Testes de tratamento de erros HTTP."""

    @pytest.mark.asyncio
    async def test_erro_autenticacao(self, adaptador, requisicao_basica):
        """HTTP 401 deve lançar TokenInvalidoError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(TokenInvalidoError):
                await adaptador.enviar_prompt(requisicao_basica)

    @pytest.mark.asyncio
    async def test_rate_limit(self, adaptador, requisicao_basica):
        """HTTP 429 deve lançar LimiteExcedidoError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(LimiteExcedidoError):
                await adaptador.enviar_prompt(requisicao_basica)

    @pytest.mark.asyncio
    async def test_erro_servidor(self, adaptador, requisicao_basica):
        """HTTP 500 deve lançar ProvedorIndisponivelError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(ProvedorIndisponivelError):
                await adaptador.enviar_prompt(requisicao_basica)

    @pytest.mark.asyncio
    async def test_timeout(self, adaptador, requisicao_basica):
        """Timeout deve lançar TimeoutExcedidoError."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")
            with pytest.raises(TimeoutExcedidoError):
                await adaptador.enviar_prompt(requisicao_basica)

    @pytest.mark.asyncio
    async def test_erro_conexao(self, adaptador, requisicao_basica):
        """Erro de conexão deve lançar ProvedorIndisponivelError."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            with pytest.raises(ProvedorIndisponivelError):
                await adaptador.enviar_prompt(requisicao_basica)

    @pytest.mark.asyncio
    async def test_resposta_invalida_sem_choices(self, adaptador, requisicao_basica):
        """Resposta sem choices deve lançar RespostaInesperadaError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(RespostaInesperadaError):
                await adaptador.enviar_prompt(requisicao_basica)

    @pytest.mark.asyncio
    async def test_resposta_invalida_sem_message(self, adaptador, requisicao_basica):
        """Resposta sem message.content deve lançar RespostaInesperadaError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"index": 0}]}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(RespostaInesperadaError):
                await adaptador.enviar_prompt(requisicao_basica)


class TestSeguranca:
    """Testes de segurança — API key nunca deve aparecer em logs/mensagens."""

    def test_api_key_nao_acessivel_publicamente(self, adaptador):
        """API key não deve ser acessível via atributos públicos."""
        assert not hasattr(adaptador, 'api_key')

    @pytest.mark.asyncio
    async def test_api_key_nao_aparece_em_erro_autenticacao(self):
        """Mensagem de erro 401 não deve conter API key."""
        adaptador = DeepSeekAdapter(api_key="sk-secreta-123")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            try:
                await adaptador.enviar_prompt(RequisicaoIA(prompt="Teste"))
            except TokenInvalidoError as e:
                assert "sk-secreta" not in str(e)
                assert "sk-secreta" not in str(e.contexto)

    @pytest.mark.asyncio
    async def test_api_key_nao_aparece_em_erro_resposta(self):
        """Mensagem de erro de resposta não deve conter API key."""
        adaptador = DeepSeekAdapter(api_key="sk-secreta-456")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            try:
                await adaptador.enviar_prompt(RequisicaoIA(prompt="Teste"))
            except RespostaInesperadaError as e:
                assert "sk-secreta" not in str(e)
                assert "sk-secreta" not in str(e.contexto)
