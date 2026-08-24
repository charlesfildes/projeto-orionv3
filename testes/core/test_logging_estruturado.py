"""
Testes unitários para o módulo de logging estruturado.
"""

import json
import logging
import pytest
from unittest.mock import patch, MagicMock

from mestre_ia.core.configuracao import Ambiente, ConfiguracaoLogging
from mestre_ia.core.logging_estruturado import (
    FormatadorJSON,
    FormatadorTexto,
    LoggerComContexto,
    CHAVES_SENSIVEIS,
    configurar_logging,
    definir_correlacao_id,
    mascarar_valor,
    obter_correlacao_id,
    obter_logger,
    resetar_configuracao_logging,
)


class TestMascararValor:
    """Testes para mascaramento de dados sensíveis."""

    def test_mascarar_string_padrao_sensivel(self):
        """Deve redigir strings que contêm padrões sensíveis."""
        assert mascarar_valor("sk-1234567890abcdef") == "[REDACTED]"
        assert mascarar_valor("Bearer token_abc_123") == "[REDACTED]"
        assert mascarar_valor("api_key=secret_key") == "[REDACTED]"
        assert mascarar_valor("texto comum sem segredos") == "texto comum sem segredos"

    def test_mascarar_dicionario(self):
        """Deve mascarar valores de chaves sensíveis em dicionários."""
        dados = {
            "usuario": "carlos",
            "api_key": "sk-123",
            "jwt_secret": "minha_chave_secreta",
            "detalhes": {
                "password": "senha_secreta",
                "normal": "valor_normal"
            }
        }
        resultado = mascarar_valor(dados)

        assert resultado["usuario"] == "carlos"
        assert resultado["api_key"] == "[REDACTED]"
        assert resultado["jwt_secret"] == "[REDACTED]"
        assert resultado["detalhes"]["password"] == "[REDACTED]"
        assert resultado["detalhes"]["normal"] == "valor_normal"

    def test_mascarar_listas_e_tuples(self):
        """Deve mascarar itens sensíveis em listas e tuplas."""
        lista = ["comum", "sk-secret", {"token": "123"}]
        resultado = mascarar_valor(lista)

        assert resultado[0] == "comum"
        assert resultado[1] == "[REDACTED]"
        assert resultado[2]["token"] == "[REDACTED]"


class TestFormatadorJSON:
    """Testes para o formatador JSON."""

    def test_formatar_registro_basico(self):
        """Deve formatar LogRecord para JSON estruturado."""
        formatador = FormatadorJSON(ambiente=Ambiente.DESENVOLVIMENTO)
        record = logging.LogRecord(
            name="mestre_ia.teste",
            level=logging.INFO,
            pathname="teste.py",
            lineno=10,
            msg="Mensagem de teste",
            args=(),
            exc_info=None
        )

        saida_str = formatador.format(record)
        saida = json.loads(saida_str)

        assert saida["level"] == "INFO"
        assert saida["logger_name"] == "mestre_ia.teste"
        assert saida["message"] == "Mensagem de teste"
        assert saida["environment"] == Ambiente.DESENVOLVIMENTO.value
        assert "timestamp" in saida

    def test_formatar_com_extra_e_mascaramento(self):
        """Deve incluir e mascarar campos extras."""
        formatador = FormatadorJSON(ambiente=Ambiente.PRODUCAO)
        record = logging.LogRecord(
            name="mestre_ia.teste",
            level=logging.WARNING,
            pathname="teste.py",
            lineno=10,
            msg="Aviso com token",
            args=(),
            exc_info=None
        )
        record.extra = {"api_key": "sk-12345", "user_id": "99"}

        saida_str = formatador.format(record)
        saida = json.loads(saida_str)

        assert saida["environment"] == Ambiente.PRODUCAO.value
        assert saida["extra"]["api_key"] == "[REDACTED]"
        assert saida["extra"]["user_id"] == "99"

    def test_formatar_com_correlacao_id(self):
        """Deve capturar e incluir correlation_id do ContextVar."""
        definir_correlacao_id("req-12345")
        try:
            formatador = FormatadorJSON()
            record = logging.LogRecord(
                name="mestre_ia.teste",
                level=logging.INFO,
                pathname="teste.py",
                lineno=10,
                msg="Log rastreado",
                args=(),
                exc_info=None
            )
            saida_str = formatador.format(record)
            saida = json.loads(saida_str)

            assert saida["correlacao_id"] == "req-12345"
        finally:
            definir_correlacao_id(None)


class TestFormatadorTexto:
    """Testes para o formatador de texto legível."""

    def test_formatar_texto_simples(self):
        """Deve formatar registro como texto contendo as informações."""
        formatador = FormatadorTexto()
        record = logging.LogRecord(
            name="mestre_ia.modulo",
            level=logging.ERROR,
            pathname="teste.py",
            lineno=10,
            msg="Erro grave",
            args=(),
            exc_info=None
        )

        saida = formatador.format(record)
        assert "[ERROR]" in saida
        assert "mestre_ia.modulo" in saida
        assert "Erro grave" in saida


class TestConfigurarLoggingEObterLogger:
    """Testes de inicialização do logger global e fábrica de loggers."""

    def setup_method(self):
        resetar_configuracao_logging()

    def test_obter_logger_prefixo(self):
        """Logger deve ter o namespace mestre_ia."""
        logger = obter_logger("servico.teste")
        assert logger.name == "mestre_ia.servico.teste"

        logger_com_prefixo = obter_logger("mestre_ia.servico.teste")
        assert logger_com_prefixo.name == "mestre_ia.servico.teste"

    def test_configurar_logging_global(self):
        """Deve configurar root logger adequadamente."""
        config = ConfiguracaoLogging(nivel="DEBUG", formato="json")
        configurar_logging(config, ambiente=Ambiente.DESENVOLVIMENTO)

        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) >= 1
        assert isinstance(root.handlers[0].formatter, FormatadorJSON)


class TestLoggerComContexto:
    """Testes para o wrapper LoggerComContexto."""

    def test_wrapper_adiciona_contexto(self):
        """Wrapper deve incluir contexto fixo ao enviar log."""
        mock_logger = MagicMock()
        contextual = LoggerComContexto(mock_logger, modulo="autenticacao", versao="1.0")

        contextual.info("Login realizado", usuario_id="usr_123")

        mock_logger.log.assert_called_once_with(
            logging.INFO,
            "Login realizado",
            extra={
                "extra": {
                    "modulo": "autenticacao",
                    "versao": "1.0",
                    "usuario_id": "usr_123"
                }
            }
        )

    def test_com_contexto_adicional(self):
        """Deve encadear contextos criando uma nova instância."""
        mock_logger = MagicMock()
        base = LoggerComContexto(mock_logger, app="orion")
        sub = base.com_contexto(modulo="medicina")

        sub.warning("Alerta")

        mock_logger.log.assert_called_once_with(
            logging.WARNING,
            "Alerta",
            extra={
                "extra": {
                    "app": "orion",
                    "modulo": "medicina"
                }
            }
        )
