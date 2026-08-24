import pytest
from mestre_ia.dominio.entidades import NivelEvidencia, ReferenciaCientifica, Evidencia, Paciente, Diagnostico

class TestNivelEvidencia:
    def test_comparacao_niveis(self):
        assert NivelEvidencia.META_ANALISE.value < NivelEvidencia.OPINIAO_ESPECIALISTA.value

class TestReferenciaCientifica:
    def test_criacao_valida(self):
        ref = ReferenciaCientifica(titulo="Estudo", autores=["Silva, J."], ano=2024)
        assert ref.titulo == "Estudo"

class TestPaciente:
    def test_criacao_valida(self):
        paciente = Paciente(nome="Maria", idade=45)
        assert paciente.nome == "Maria"
