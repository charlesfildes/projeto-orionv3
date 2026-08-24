"""
Testes de cobertura para o Orquestrador.
API real: Orquestrador(provedores: Dict, capacidades: RegistroCapacidades)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mestre_ia.aplicacao.orquestrador import Orquestrador
from mestre_ia.core.contratos import (
    RequisicaoIA,
    RespostaIA,
    TipoProvedorIA,
)
from mestre_ia.core.capacidades import (
    DominioTarefa,
    PerfilCapacidade,
    RegistroCapacidades,
)
from mestre_ia.core.excecoes import ProvedorIndisponivelError


class FakeProvedor:
    """Provedor fake."""

    VERSAO_CONTRATO = "1.0"

    def __init__(self, nome: str = "fake"):
        self._nome = nome
        self.enviar_prompt = AsyncMock()
        self.enviar_prompt_streaming = MagicMock()

    @property
    def provedor(self):
        return TipoProvedorIA.PERSONALIZADO

    @property
    def modelos_disponiveis(self):
        return ["fake-model"]


@pytest.fixture
def registro():
    """Registro com perfil fake."""
    reg = RegistroCapacidades()
    reg.registrar(PerfilCapacidade(
        modelo="fake-model",
        provedor="fake",
        scores={DominioTarefa.CONVERSACAO: 0.9},
    ))
    return reg


@pytest.fixture
def provedor_fake():
    """Provedor fake."""
    fake = FakeProvedor()
    fake.enviar_prompt.return_value = RespostaIA(
        conteudo="Resposta fake",
        provedor=TipoProvedorIA.PERSONALIZADO,
        modelo="fake-model",
        tokens_entrada=5,
        tokens_saida=3,
        tempo_resposta_ms=100.0,
    )
    return fake


@pytest.fixture
def orquestrador(registro, provedor_fake):
    """Orquestrador com provedor fake como DICIONÁRIO."""
    return Orquestrador(
        provedores={"fake": provedor_fake},
        capacidades=registro,
    )


class TestProcessarAsync:
    """Testes do método processar."""

    @pytest.mark.asyncio
    async def test_processar_async_fluxo_direto(self, orquestrador, provedor_fake):
        """Deve processar e retornar RespostaIA."""
        requisicao = RequisicaoIA(prompt="Teste async")

        resposta = await orquestrador.processar(requisicao)

        assert isinstance(resposta, RespostaIA)
        assert resposta.conteudo == "Resposta fake"
        assert resposta.modelo == "fake-model"
        provedor_fake.enviar_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_processar_sem_provedor_lanca_erro(self):
        """Deve lançar erro quando não há provedores."""
        orquestrador_vazio = Orquestrador(
            provedores={},
            capacidades=RegistroCapacidades(),
        )

        with pytest.raises(ProvedorIndisponivelError):
            await orquestrador_vazio.processar(RequisicaoIA(prompt="Teste"))

    @pytest.mark.asyncio
    async def test_processar_erro_provedor_propagado(self, orquestrador, provedor_fake):
        """Deve propagar exceção do provedor."""
        from mestre_ia.core.excecoes import TokenInvalidoError
        provedor_fake.enviar_prompt.side_effect = TokenInvalidoError(provedor="fake")

        with pytest.raises(TokenInvalidoError):
            await orquestrador.processar(RequisicaoIA(prompt="Teste"))


class TestSelecaoProvedor:
    """Testes do método _selecionar_provedor."""

    def test_selecionar_provedor_existente(self, orquestrador):
        """Deve selecionar provedor compatível."""
        provedor = orquestrador._selecionar_provedor(DominioTarefa.CONVERSACAO)
        assert provedor is not None

    def test_selecionar_provedor_sem_provedores(self):
        """Deve retornar None quando não há provedores."""
        orquestrador_vazio = Orquestrador(
            provedores={},
            capacidades=RegistroCapacidades(),
        )
        provedor = orquestrador_vazio._selecionar_provedor(DominioTarefa.CONVERSACAO)
        assert provedor is None


class TestExtracaoDominio:
    """Testes do método _extrair_dominio."""

    def test_dominio_valido(self, orquestrador):
        """Deve extrair DominioTarefa válido."""
        req = RequisicaoIA(prompt="Teste", metadados={"dominio": "medicina"})
        dominio = orquestrador._extrair_dominio(req)
        assert dominio == DominioTarefa.MEDICINA
        assert dominio.value == "medicina"

    def test_dominio_invalido(self, orquestrador):
        """Deve retornar CONVERSACAO para domínio inválido."""
        req = RequisicaoIA(prompt="Teste", metadados={"dominio": "invalido"})
        dominio = orquestrador._extrair_dominio(req)
        assert dominio == DominioTarefa.CONVERSACAO

    def test_dominio_sem_metadados(self, orquestrador):
        """Deve retornar CONVERSACAO sem metadados."""
        req = RequisicaoIA(prompt="Teste")
        dominio = orquestrador._extrair_dominio(req)
        assert dominio == DominioTarefa.CONVERSACAO
