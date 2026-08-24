"""
Testes unitários focados nas entidades do domínio e métodos de alteração (Paciente e Diagnostico).
"""

import pytest
from mestre_ia.dominio.entidades import Paciente, Diagnostico, Evidencia, NivelEvidencia


class TestPacienteMetodosAlteracao:
    """Suíte de testes para os métodos de mutação e regras do Paciente."""

    @pytest.fixture
    def paciente_valido(self):
        return Paciente(nome="Carlos Silva", idade=45)

    @pytest.fixture
    def diagnostico_valido(self):
        return Diagnostico(condicao="Hipertensão Arterial", probabilidade=0.85)

    def test_adicionar_sintoma_valido(self, paciente_valido):
        """Deve adicionar um sintoma válido e higienizado à lista do paciente."""
        paciente_valido.adicionar_sintoma(" Cefaleia ")
        assert "Cefaleia" in paciente_valido.sintomas
        assert len(paciente_valido.sintomas) == 1

    def test_adicionar_sintoma_duplicado_nao_repetition(self, paciente_valido):
        """Não deve adicionar sintomas repetidos."""
        paciente_valido.adicionar_sintoma("Febre")
        paciente_valido.adicionar_sintoma("Febre")
        assert paciente_valido.sintomas.count("Febre") == 1

    def test_adicionar_sintoma_vazio_ignorado(self, paciente_valido):
        """Não deve adicionar strings vazias ou compostas apenas por espaços."""
        paciente_valido.adicionar_sintoma("")
        paciente_valido.adicionar_sintoma("   ")
        assert len(paciente_valido.sintomas) == 0

    def test_adicionar_diagnostico_sucesso(self, paciente_valido, diagnostico_valido):
        """Deve adicionar um objeto Diagnostico à lista do paciente."""
        paciente_valido.adicionar_diagnostico(diagnostico_valido)
        assert len(paciente_valido.diagnosticos) == 1
        assert paciente_valido.diagnosticos[0].condicao == "Hipertensão Arterial"

    def test_adicionar_multiplos_diagnosticos(self, paciente_valido):
        """Deve ser capaz de acumular múltiplos diagnósticos."""
        diag1 = Diagnostico(condicao="Gripe", probabilidade=0.9)
        diag2 = Diagnostico(condicao="Dengue", probabilidade=0.4)
        
        paciente_valido.adicionar_diagnostico(diag1)
        paciente_valido.adicionar_diagnostico(diag2)
        
        assert len(paciente_valido.diagnosticos) == 2


class TestDiagnosticoPropriedades:
    """Testes para propriedades e classificações de confiança do Diagnóstico."""

    def test_probabilidade_percentual(self):
        """Garante a conversão correta da probabilidade para porcentagem."""
        diag = Diagnostico(condicao="Diabetes Tipo 2", probabilidade=0.75)
        assert diag.probabilidade_percentual == 75.0

    @pytest.mark.parametrize("prob,classificacao_esperada", [
        (0.95, "ALTA CONFIANÇA"),
        (0.90, "ALTA CONFIANÇA"),
        (0.85, "CONFIANÇA MODERADA"),
        (0.70, "CONFIANÇA MODERADA"),
        (0.60, "BAIXA CONFIANÇA"),
        (0.50, "BAIXA CONFIANÇA"),
        (0.30, "ESPECULATIVO - MAIS EXAMES RECOMENDADOS"),
    ])
    def test_classificacao_confianca(self, prob, classificacao_esperada):
        """Valida as faixas de confiança com base na probabilidade."""
        diag = Diagnostico(condicao="Teste", probabilidade=prob)
        assert diag.classificacao_confianca == classificacao_esperada
