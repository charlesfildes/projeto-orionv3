"""
Testes unitários para o Orquestrador V1.

Utiliza fakes dos contratos — sem chamadas reais à API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mestre_ia.aplicacao.orquestrador import Orquestrador
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
    ProvedorIndisponivelError,
)


class FakeProvedor:
    """Implementação fake de IAProviderPort para testes."""

    VERSAO_CONTRATO = "1.0"

    def __init__(self, nome: str = "fake", modelos: list = None):
        self._nome = nome
        self._modelos = modelos or ["fake-model"]
        self.enviar_prompt = AsyncMock()
        self.enviar_prompt_streaming = MagicMock()

    @property
    def provedor(self) -> TipoProvedorIA:
        return TipoProvedorIA.PERSONALIZADO

    @property
    def modelos_disponiveis(self):
        return self._modelos


@pytest.fixture
def registro():
    """Registro de capacidades com perfil fake."""
    reg = RegistroCapacidades()
    reg.registrar(PerfilCapacidade(
        modelo="fake-model",
        provedor="fake",
        scores={DominioTarefa.MEDICINA: 0.9},
    ))
    return reg


@pytest.fixture
def provedor_fake():
    """Provedor fake com comportamento mockado."""
    fake = FakeProvedor(nome="fake")
    fake.enviar_prompt.return_value = RespostaIA(
        conteudo="Resposta fake",
        provedor=TipoProvedorIA.PERSONALIZADO,
        modelo="fake-model",
    )
    return fake


@pytest.fixture
def orquestrador(registro, provedor_fake):
    """Orquestrador com provedor fake."""
    return Orquestrador(
        provedores={"fake": provedor_fake},
        capacidades=registro,
    )


@pytest.fixture
def requisicao_medicina():
    """Requisição com domínio medicina."""
    return RequisicaoIA(
        prompt="Diagnóstico de hipertensão",
        metadados={"dominio": "medicina"},
    )


@pytest.fixture
def requisicao_sem_dominio():
    """Requisição sem domínio especificado."""
    return RequisicaoIA(prompt="Olá, como vai?")


class TestCriacao:
    """Testes de inicialização do Orquestrador."""

    def test_criacao_valida(self, registro, provedor_fake):
        """Deve criar Orquestrador com parâmetros válidos."""
        orquestrador = Orquestrador(
            provedores={"fake": provedor_fake},
            capacidades=registro,
        )
        assert orquestrador is not None

    def test_criacao_sem_provedores(self, registro):
        """Deve criar Orquestrador sem provedores."""
        orquestrador = Orquestrador(provedores={}, capacidades=registro)
        assert orquestrador is not None


class TestProcessar:
    """Testes do método processar."""

    @pytest.mark.asyncio
    async def test_processar_com_dominio(self, orquestrador, requisicao_medicina, provedor_fake):
        """Deve encaminhar requisição com domínio ao provedor compatível."""
        resposta = await orquestrador.processar(requisicao_medicina)

        assert isinstance(resposta, RespostaIA)
        assert resposta.conteudo == "Resposta fake"
        provedor_fake.enviar_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_processar_sem_dominio(self, orquestrador, requisicao_sem_dominio, provedor_fake):
        """Deve usar CONVERSACAO quando domínio não especificado."""
        resposta = await orquestrador.processar(requisicao_sem_dominio)

        assert isinstance(resposta, RespostaIA)
        provedor_fake.enviar_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_processar_propaga_requisicao(self, orquestrador, requisicao_medicina, provedor_fake):
        """Deve passar a RequisicaoIA para o provedor."""
        await orquestrador.processar(requisicao_medicina)

        chamada = provedor_fake.enviar_prompt.call_args
        requisicao_enviada = chamada[0][0]
        assert requisicao_enviada.id == requisicao_medicina.id

    @pytest.mark.asyncio
    async def test_processar_com_timeout(self, orquestrador, requisicao_medicina, provedor_fake):
        """Deve propagar timeout_ms para o provedor."""
        await orquestrador.processar(requisicao_medicina, timeout_ms=5000)

        provedor_fake.enviar_prompt.assert_called_once()
        chamada = provedor_fake.enviar_prompt.call_args
        assert chamada[1].get("timeout_ms") == 5000


class TestSelecaoProvedor:
    """Testes de seleção de provedor."""

    def test_selecionar_por_dominio(self, orquestrador):
        """Deve selecionar provedor compatível com o domínio."""
        provedor = orquestrador._selecionar_provedor(DominioTarefa.MEDICINA)
        assert provedor is not None

    def test_dominio_sem_provedor_compativel(self, orquestrador):
        """Deve retornar fallback quando não há compatível."""
        provedor = orquestrador._selecionar_provedor(DominioTarefa.IMAGENS)
        assert provedor is not None

    def test_sem_provedores_disponiveis(self, registro):
        """Deve retornar None quando não há provedores."""
        orquestrador = Orquestrador(provedores={}, capacidades=registro)
        provedor = orquestrador._selecionar_provedor(DominioTarefa.MEDICINA)
        assert provedor is None

    @pytest.mark.asyncio
    async def test_sem_provedor_lanca_erro(self, registro):
        """Deve lançar ProvedorIndisponivelError quando não há provedores."""
        orquestrador = Orquestrador(provedores={}, capacidades=registro)
        with pytest.raises(ProvedorIndisponivelError):
            await orquestrador.processar(RequisicaoIA(prompt="Teste"))


class TestExtracaoDominio:
    """Testes de extração de domínio da requisição."""

    def test_dominio_valido(self, orquestrador):
        """Deve extrair domínio dos metadados."""
        req = RequisicaoIA(prompt="Teste", metadados={"dominio": "medicina"})
        dominio = orquestrador._extrair_dominio(req)
        assert dominio == DominioTarefa.MEDICINA

    def test_dominio_invalido_retorna_conversacao(self, orquestrador):
        """Deve retornar CONVERSACAO para domínio inválido."""
        req = RequisicaoIA(prompt="Teste", metadados={"dominio": "invalido"})
        dominio = orquestrador._extrair_dominio(req)
        assert dominio == DominioTarefa.CONVERSACAO

    def test_sem_dominio_retorna_conversacao(self, orquestrador):
        """Deve retornar CONVERSACAO quando não há metadados."""
        req = RequisicaoIA(prompt="Teste")
        dominio = orquestrador._extrair_dominio(req)
        assert dominio == DominioTarefa.CONVERSACAO


class TestPropagacaoErros:
    """Testes de propagação de exceções do provedor."""

    @pytest.mark.asyncio
    async def test_propaga_erro_do_provedor(self, orquestrador, requisicao_medicina, provedor_fake):
        """Deve propagar exceções lançadas pelo provedor."""
        from mestre_ia.core.excecoes import TokenInvalidoError
        provedor_fake.enviar_prompt.side_effect = TokenInvalidoError(provedor="fake")

        with pytest.raises(TokenInvalidoError):
            await orquestrador.processar(requisicao_medicina)


class TestDesacoplamento:
    """Verifica que o Orquestrador não conhece implementações concretas."""

    def test_nao_conhece_api_key(self):
        """Orquestrador não deve ter atributo api_key."""
        orquestrador = Orquestrador(
            provedores={},
            capacidades=RegistroCapacidades(),
        )
        assert not hasattr(orquestrador, 'api_key')
        assert not hasattr(orquestrador, '_api_key')
