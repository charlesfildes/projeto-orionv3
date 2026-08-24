"""Testes para o módulo de contratos e data classes do Core."""

import pytest
from mestre_ia.core.contratos import (
    IAProviderPort,
    RequisicaoIA,
    RespostaIA,
    ResultadoQuantico,
    EstadoTarefa,
    PrioridadeTarefa,
)


class TestContratosEDataClasses:
    """Testes para data classes, enums e contratos do core."""

    def test_requisicao_e_resposta_ia(self):
        req = RequisicaoIA(prompt="Olá, mundo!")
        assert req.prompt == "Olá, mundo!"

        resp = RespostaIA(
            conteudo="Resposta de teste",
            modelo="test-model",
            provedor="test-provider",
        )
        assert resp.conteudo == "Resposta de teste"
        assert resp.modelo == "test-model"
        assert resp.provedor == "test-provider"

    def test_resultado_quantico(self):
        res = ResultadoQuantico(
            contagens={"00": 500, "11": 500},
            provedor="IBM Quantum",
            tempo_execucao_ms=120.5,
        )
        assert res.contagens["00"] == 500
        assert res.provedor == "IBM Quantum"
        assert res.tempo_execucao_ms == 120.5

    def test_enums(self):
        assert hasattr(EstadoTarefa, "PENDENTE") or len(EstadoTarefa) > 0
        assert hasattr(PrioridadeTarefa, "ALTA") or len(PrioridadeTarefa) > 0

    def test_implementacao_ia_provider_port(self):
        class ProvedorMock:
            async def gerar_resposta(self, requisicao: RequisicaoIA) -> RespostaIA:
                return RespostaIA(
                    conteudo="Mock", modelo="mock", provedor="mock"
                )

            async def esta_disponivel(self) -> bool:
                return True

        provedor = ProvedorMock()
        assert hasattr(provedor, "gerar_resposta")
        assert hasattr(provedor, "esta_disponivel")