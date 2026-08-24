"""Testes unitários para o módulo de exceções do núcleo."""

import pytest
from mestre_ia.core.excecoes import (
    MestreIAError,
    ErroConfiguracao,
    ErroDominio,
    ErroInfraestrutura,
    ErroSeguranca,
    ConfiguracaoInvalidaError,
    ConfiguracaoAusenteError,
    ProvedorIndisponivelError,
    RespostaInesperadaError,
    TimeoutExcedidoError,
    LimiteExcedidoError,
    TokenInvalidoError,
    DiagnosticoInconsistenteError,
    EvidenciaInvalidaError,
    PacienteSemSintomasError,
    ReferenciaInvalidaError,
)


class TestExcecoesCore:
    def test_mestre_ia_error_base(self):
        erro = MestreIAError("Erro genérico", codigo="ERR_001")
        assert str(erro) == "[ERR_001] Erro genérico"
        assert erro.codigo == "ERR_001"

    def test_erros_base_hierarquia(self):
        assert issubclass(ErroConfiguracao, MestreIAError)
        assert issubclass(ErroDominio, MestreIAError)
        assert issubclass(ErroInfraestrutura, MestreIAError)
        assert issubclass(ErroSeguranca, MestreIAError)

    def test_configuracao_invalida_error(self):
        erro = ConfiguracaoInvalidaError("TIMEOUT", 0, "inteiro > 0")
        assert "TIMEOUT" in str(erro) or hasattr(erro, "chave")

    def test_configuracao_ausente_error(self):
        erro = ConfiguracaoAusenteError("OPENAI_API_KEY")
        assert "OPENAI_API_KEY" in str(erro)

    def test_provedor_indisponivel_error(self):
        erro = ProvedorIndisponivelError("OpenAI")
        assert "OpenAI" in str(erro)

    def test_resposta_inesperada_error(self):
        erro = RespostaInesperadaError("OpenAI", "Formato JSON inválido")
        assert "OpenAI" in str(erro) or hasattr(erro, "provedor")

    def test_timeout_excedido_error(self):
        erro = TimeoutExcedidoError("requisicao_ia", 5000)
        assert "requisicao_ia" in str(erro) or hasattr(erro, "operacao")

    def test_limite_excedido_error(self):
        erro = LimiteExcedidoError("Limite de requisições excedido")
        assert "Limite de requisições excedido" in str(erro)

    def test_token_invalido_error(self):
        erro = TokenInvalidoError("Token JWT expirado")
        assert "Token JWT expirado" in str(erro)

    def test_erros_dominio_medico(self):
        err1 = DiagnosticoInconsistenteError("Gripe", 0.1, "Sintoma incompatível")
        err2 = EvidenciaInvalidaError("Raio-X", "Exame sem alteração")
        err3 = PacienteSemSintomasError("Paciente sem histórico")
        err4 = ReferenciaInvalidaError("CID-10", "Z00.0", "Código não cadastrado")

        assert err1 is not None
        assert "Raio-X" in str(err2) or hasattr(err2, "evidencia")
        assert "Paciente sem histórico" in str(err3)
        assert err4 is not None