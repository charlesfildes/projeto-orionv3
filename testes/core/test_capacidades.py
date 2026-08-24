"""
Testes unitários para o módulo de Registro de Capacidades (core/capacidades.py).
"""

import pytest
from mestre_ia.core.capacidades import (
    DominioTarefa,
    PerfilCapacidade,
    RegistroCapacidades,
)


class TestPerfilCapacidade:
    """Testes para a dataclass PerfilCapacidade."""

    def test_score_para_dominio_existente(self):
        perfil = PerfilCapacidade(
            modelo="deepseek-chat",
            provedor="deepseek",
            scores={
                DominioTarefa.CONVERSACAO: 0.9,
                DominioTarefa.PROGRAMACAO: 0.85,
            },
        )
        assert perfil.score_para(DominioTarefa.CONVERSACAO) == 0.9
        assert perfil.score_para(DominioTarefa.PROGRAMACAO) == 0.85

    def test_score_para_dominio_inexistente_retorna_zero(self):
        perfil = PerfilCapacidade(
            modelo="deepseek-chat",
            provedor="deepseek",
            scores={DominioTarefa.CONVERSACAO: 0.9},
        )
        assert perfil.score_para(DominioTarefa.MEDICINA) == 0.0

    def test_suporta_dominio(self):
        perfil = PerfilCapacidade(
            modelo="deepseek-chat",
            provedor="deepseek",
            scores={
                DominioTarefa.CONVERSACAO: 0.9,
                DominioTarefa.MATEMATICA: 0.0,
            },
        )
        assert perfil.suporta(DominioTarefa.CONVERSACAO) is True
        assert perfil.suporta(DominioTarefa.MATEMATICA) is False
        assert perfil.suporta(DominioTarefa.DIREITO) is False

    def test_eh_especialista(self):
        perfil = PerfilCapacidade(
            modelo="deepseek-reasoner",
            provedor="deepseek",
            scores={
                DominioTarefa.RACIOCINIO_LOGICO: 0.95,
                DominioTarefa.MEDICINA: 0.8,
                DominioTarefa.TRADUCAO: 0.79,
            },
        )
        assert perfil.eh_especialista(DominioTarefa.RACIOCINIO_LOGICO) is True
        assert perfil.eh_especialista(DominioTarefa.MEDICINA) is True
        assert perfil.eh_especialista(DominioTarefa.TRADUCAO) is False


class TestRegistroCapacidades:
    """Testes para a classe RegistroCapacidades."""

    @pytest.fixture
    def registro(self):
        return RegistroCapacidades()

    @pytest.fixture
    def perfil_deepseek(self):
        return PerfilCapacidade(
            modelo="deepseek-chat",
            provedor="deepseek",
            scores={
                DominioTarefa.CONVERSACAO: 0.9,
                DominioTarefa.PROGRAMACAO: 0.85,
                DominioTarefa.MEDICINA: 0.7,
            },
        )

    @pytest.fixture
    def perfil_gpt4(self):
        return PerfilCapacidade(
            modelo="gpt-4o",
            provedor="openai",
            scores={
                DominioTarefa.CONVERSACAO: 0.95,
                DominioTarefa.MEDICINA: 0.85,
                DominioTarefa.IMAGENS: 0.9,
            },
        )

    def test_registrar_e_obter_perfil(self, registro, perfil_deepseek):
        registro.registrar(perfil_deepseek)
        perfil_obtido = registro.obter_perfil("deepseek-chat")

        assert perfil_obtido is not None
        assert perfil_obtido.modelo == "deepseek-chat"
        assert perfil_obtido.provedor == "deepseek"

    def test_obter_perfil_inexistente_retorna_none(self, registro):
        assert registro.obter_perfil("modelo-fantasma") is None

    def test_remover_modelo(self, registro, perfil_deepseek):
        registro.registrar(perfil_deepseek)
        assert registro.obter_perfil("deepseek-chat") is not None

        registro.remover("deepseek-chat")
        assert registro.obter_perfil("deepseek-chat") is None

    def test_remover_modelo_inexistente_nao_causa_erro(self, registro):
        registro.remover("modelo-inexistente")  # Não deve lançar exceção

    def test_buscar_por_dominio(self, registro, perfil_deepseek, perfil_gpt4):
        registro.registrar(perfil_deepseek)
        registro.registrar(perfil_gpt4)

        medicina_cand = registro.buscar_por_dominio(DominioTarefa.MEDICINA)
        assert len(medicina_cand) == 2

        prog_cand = registro.buscar_por_dominio(DominioTarefa.PROGRAMACAO)
        assert len(prog_cand) == 1
        assert prog_cand[0].modelo == "deepseek-chat"

        imagens_cand = registro.buscar_por_dominio(DominioTarefa.IMAGENS)
        assert len(imagens_cand) == 1
        assert imagens_cand[0].modelo == "gpt-4o"

        quantum_cand = registro.buscar_por_dominio(DominioTarefa.QUANTUM)
        assert len(quantum_cand) == 0

    def test_listar_todos(self, registro, perfil_deepseek, perfil_gpt4):
        assert len(registro.listar_todos()) == 0

        registro.registrar(perfil_deepseek)
        registro.registrar(perfil_gpt4)

        todos = registro.listar_todos()
        assert len(todos) == 2
        modelos = [p.modelo for p in todos]
        assert "deepseek-chat" in modelos
        assert "gpt-4o" in modelos

    def test_obter_provedor_para_modelo(self, registro, perfil_deepseek):
        registro.registrar(perfil_deepseek)

        provedor = registro.obter_provedor_para_modelo("deepseek-chat")
        assert provedor == "deepseek"

        provedor_inexistente = registro.obter_provedor_para_modelo("modelo-inexistente")
        assert provedor_inexistente is None
