"""
Testes unitários para MemoriaCurtoPrazo baseados na API real:
- __init__(limite_mensagens: int = 10)
- adicionar_mensagem(papel: str, conteudo: str)
- obter_historico() -> List[Dict[str, str]]
- limpar()
"""

import pytest
from mestre_ia.memoria.curto_prazo import MemoriaCurtoPrazo


class TestInicializacao:
    """Testes da inicialização da MemoriaCurtoPrazo."""

    def test_inicializacao_padrao(self):
        """Deve iniciar com histórico vazio e limite padrão 10."""
        memoria = MemoriaCurtoPrazo()
        assert memoria._limite == 10
        assert memoria.obter_historico() == []

    def test_inicializacao_limite_personalizado(self):
        """Deve permitir definir um limite_mensagens customizado."""
        memoria = MemoriaCurtoPrazo(limite_mensagens=5)
        assert memoria._limite == 5


class TestAdicionarMensagem:
    """Testes do método adicionar_mensagem."""

    def test_adicionar_mensagem_unica(self):
        """Deve adicionar uma mensagem corretamente no histórico."""
        memoria = MemoriaCurtoPrazo()
        memoria.adicionar_mensagem("user", "Olá!")

        historico = memoria.obter_historico()
        assert len(historico) == 1
        assert historico[0] == {"role": "user", "content": "Olá!"}

    def test_adicionar_multiplas_mensagens(self):
        """Deve acumular mensagens mantendo papéis e sequências."""
        memoria = MemoriaCurtoPrazo()
        memoria.adicionar_mensagem("user", "Olá")
        memoria.adicionar_mensagem("assistant", "Oi, como posso ajudar?")

        historico = memoria.obter_historico()
        assert len(historico) == 2
        assert historico[0] == {"role": "user", "content": "Olá"}
        assert historico[1] == {"role": "assistant", "content": "Oi, como posso ajudar?"}


class TestJanelaDeslizanteLimite:
    """Testes de truncagem de histórico quando atinge o limite."""

    def test_respeita_limite_mensagens(self):
        """Deve remover a mensagem mais antiga (FIFO) ao ultrapassar o limite."""
        memoria = MemoriaCurtoPrazo(limite_mensagens=3)
        
        memoria.adicionar_mensagem("user", "Msg 1")
        memoria.adicionar_mensagem("assistant", "Msg 2")
        memoria.adicionar_mensagem("user", "Msg 3")
        memoria.adicionar_mensagem("assistant", "Msg 4")  # Ultrapassa o limite

        historico = memoria.obter_historico()
        assert len(historico) == 3
        assert historico[0]["content"] == "Msg 2"
        assert historico[1]["content"] == "Msg 3"
        assert historico[2]["content"] == "Msg 4"


class TestObterHistoricoELimpar:
    """Testes de encapsulamento e limpeza."""

    def test_obter_historico_retorna_copia(self):
        """Alterar a lista retornada por obter_historico não deve afetar a memória interna."""
        memoria = MemoriaCurtoPrazo()
        memoria.adicionar_mensagem("user", "Teste")

        historico = memoria.obter_historico()
        historico.clear()

        assert len(memoria.obter_historico()) == 1

    def test_limpar_historico(self):
        """Deve esvaziar o histórico ao chamar limpar()."""
        memoria = MemoriaCurtoPrazo()
        memoria.adicionar_mensagem("user", "M1")
        memoria.adicionar_mensagem("assistant", "M2")

        memoria.limpar()

        assert memoria.obter_historico() == []
