"""
Testes unitários para o módulo mestre_ia.dominio.servicos.
"""

import pytest
from unittest.mock import MagicMock
from mestre_ia.dominio.entidades import Paciente, Evidencia, NivelEvidencia
from mestre_ia.dominio.servicos import MotorDiagnosticoDiferencial, BaseConhecimentoMedica


class TestBaseConhecimentoMedicaInterface:
    """Garante que a classe base/interface exige implementação dos métodos."""

    def test_metodos_abstratos_lancam_not_implemented(self):
        base = BaseConhecimentoMedica()

        with pytest.raises(NotImplementedError, match="Subclasses devem implementar"):
            base.buscar_condicoes_por_sintoma("Febre")

        with pytest.raises(NotImplementedError, match="Subclasses devem implementar"):
            base.buscar_evidencias("Gripe")

        with pytest.raises(NotImplementedError, match="Subclasses devem implementar"):
            base.validar_contraindicacao("Gripe", "Aspirina")


class TestMotorDiagnosticoDiferencial:
    """Testes de lógica de negócio do motor de diagnóstico."""

    @pytest.fixture
    def mock_base_conhecimento(self):
        return MagicMock(spec=BaseConhecimentoMedica)

    def test_gerar_diagnostico_paciente_sem_sintomas_lanca_erro(self, mock_base_conhecimento):
        paciente = Paciente(nome="Carlos", idade=40)
        motor = MotorDiagnosticoDiferencial(base_conhecimento=mock_base_conhecimento)

        with pytest.raises(ValueError, match="paciente não possui sintomas registrados"):
            motor.gerar_diagnosticos(paciente)

    def test_gerar_diagnosticos_com_sucesso_e_ordenacao(self, mock_base_conhecimento):
        paciente = Paciente(nome="Maria", idade=30)
        paciente.adicionar_sintoma("Febre")
        paciente.adicionar_sintoma("Tosse")

        mock_base_conhecimento.buscar_condicoes_por_sintoma.side_effect = lambda sintoma: {
            "Febre": [("Gripe", 0.8), ("Pneumonia", 0.5)],
            "Tosse": [("Gripe", 0.6), ("Pneumonia", 0.9)],
        }.get(sintoma, [])

        evidencia_gripe = Evidencia(afirmacao="Gripe causa febre", nivel=NivelEvidencia.COORTE)
        mock_base_conhecimento.buscar_evidencias.side_effect = lambda condicao: {
            "Gripe": [evidencia_gripe],
            "Pneumonia": [],
        }.get(condicao, [])

        motor = MotorDiagnosticoDiferencial(base_conhecimento=mock_base_conhecimento)
        diagnosticos = motor.gerar_diagnosticos(paciente)

        assert len(diagnosticos) == 2
        primeiro = diagnosticos[0]
        # Pneumonia: (0.5 + 0.9)/2 = 0.7 | Gripe: (0.8 + 0.6)/2 = 0.7
        assert primeiro.probabilidade == 0.7
        assert primeiro.e_hipotese is True
        assert "de 2 sintomas relatados" in primeiro.notas

    def test_gerar_diagnosticos_limite_probabilidade_maxima(self, mock_base_conhecimento):
        paciente = Paciente(nome="João", idade=50)
        paciente.adicionar_sintoma("Dor no peito")

        mock_base_conhecimento.buscar_condicoes_por_sintoma.return_value = [("Infarto", 1.5)]
        mock_base_conhecimento.buscar_evidencias.return_value = []

        motor = MotorDiagnosticoDiferencial(base_conhecimento=mock_base_conhecimento)
        diagnosticos = motor.gerar_diagnosticos(paciente)

        assert len(diagnosticos) == 1
        assert diagnosticos[0].condicao == "Infarto"
        assert diagnosticos[0].probabilidade == 1.0
