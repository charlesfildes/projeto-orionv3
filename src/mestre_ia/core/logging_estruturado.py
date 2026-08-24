"""
Sistema de Logging Estruturado — Projeto Orion.

Fornece logging em formato JSON estruturado com suporte a:
- Saída em texto legível (desenvolvimento) ou JSON (produção)
- Máscara automática de dados sensíveis
- Contexto dinâmico (correlation_id / correlacao_id, extra) via ContextVar e wrappers
- Integração com logging padrão do Python

Uso:
    from mestre_ia.core.logging_estruturado import configurar_logging, obter_logger
    from mestre_ia.core.configuracao import ConfiguracaoLogging, Ambiente

    config = ConfiguracaoLogging()
    configurar_logging(config, Ambiente.DESENVOLVIMENTO)

    logger = obter_logger("meu_modulo")
    logger.info("Mensagem", extra={"paciente_id": "123"})
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from mestre_ia.core.configuracao import Ambiente, ConfiguracaoLogging


# Variable de contexto global para tracing / correlation_id
_CORRELACAO_ID_VAR: ContextVar[Optional[str]] = ContextVar("correlacao_id", default=None)


def definir_correlacao_id(correlacao_id: Optional[str]) -> None:
    """Define o correlation_id no contexto assíncrono/thread atual."""
    _CORRELACAO_ID_VAR.set(correlacao_id)


def obter_correlacao_id() -> Optional[str]:
    """Obtém o correlation_id do contexto atual."""
    return _CORRELACAO_ID_VAR.get()


# ============================================================================
# MÁSCARA DE DADOS SENSÍVEIS
# ============================================================================

CHAVES_SENSIVEIS = {
    "api_key", "apikey", "token", "secret", "password", "senha",
    "authorization", "jwt", "jwt_secret", "credential", "access_key",
    "access_token", "refresh_token", "private_key", "dsn", "sentry_dsn",
    "bearer_token", "client_secret", "api_secret",
}

PADROES_SENSIVEIS = [
    "sk-",
    "Bearer ",
    "Basic ",
    "api_key=",
    "token=",
    "secret=",
    "password=",
]


def mascarar_valor(valor: Any) -> Any:
    """
    Mascara recursivamente valores sensíveis em estruturas de dados.

    Args:
        valor: Qualquer valor (str, dict, list, etc.)

    Returns:
        Valor com dados sensíveis mascarados
    """
    if isinstance(valor, str):
        for padrao in PADROES_SENSIVEIS:
            if padrao.lower() in valor.lower():
                return "[REDACTED]"
        return valor
    elif isinstance(valor, dict):
        return {
            chave: "[REDACTED]" if str(chave).lower() in CHAVES_SENSIVEIS
            else mascarar_valor(v)
            for chave, v in valor.items()
        }
    elif isinstance(valor, list):
        return [mascarar_valor(item) for item in valor]
    elif isinstance(valor, tuple):
        return tuple(mascarar_valor(item) for item in valor)
    return valor


# ============================================================================
# FORMATADOR JSON ESTRUTURADO
# ============================================================================

class FormatadorJSON(logging.Formatter):
    """
    Formatador de log que emite JSON estruturado.

    Formato:
    {
        "timestamp": "2024-01-15T10:30:00.123Z",
        "level": "INFO",
        "logger_name": "meu_modulo",
        "message": "...",
        "environment": "desenvolvimento",
        "correlacao_id": "abc-123",
        ...campos extras
    }
    """

    def __init__(self, ambiente: Ambiente = Ambiente.DESENVOLVIMENTO):
        super().__init__()
        self._ambiente = ambiente

    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro como JSON."""
        env_val = self._ambiente.value if isinstance(self._ambiente, Ambiente) else str(self._ambiente)
        
        evento: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "environment": env_val,
        }

        # ContextVar ID
        correlacao_ctx = obter_correlacao_id()
        if correlacao_ctx:
            evento["correlacao_id"] = correlacao_ctx

        # Extrair correlation_id/requisicao_id do record se fornecido diretamente
        correlacao_id = getattr(record, "correlacao_id", None)
        if correlacao_id:
            evento["correlacao_id"] = correlacao_id

        requisicao_id = getattr(record, "requisicao_id", None)
        if requisicao_id:
            evento["requisicao_id"] = requisicao_id

        # Extrair campos extras
        if hasattr(record, "extra"):
            extra = getattr(record, "extra", {})
            if extra:
                evento["extra"] = mascarar_valor(extra)

        # Incluir exceção se houver
        if record.exc_info and record.exc_info[0]:
            evento["excecao_tipo"] = record.exc_info[0].__name__
            evento["excecao_mensagem"] = str(record.exc_info[1])

        try:
            return json.dumps(evento, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return json.dumps({
                "timestamp": evento["timestamp"],
                "level": evento["level"],
                "logger_name": evento["logger_name"],
                "message": record.getMessage(),
                "environment": env_val,
            }, ensure_ascii=False)


class FormatadorTexto(logging.Formatter):
    """
    Formatador de log em texto legível para desenvolvimento.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro como texto colorido."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        nivel = record.levelname
        nome = record.name
        mensagem = record.getMessage()

        cores = {
            "DEBUG": "\033[36m",
            "INFO": "\033[32m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "CRITICAL": "\033[35m",
        }
        cor = cores.get(nivel, "")
        reset = "\033[0m"

        extra_str = ""
        if hasattr(record, "extra") and record.extra:
            extra_mascarado = mascarar_valor(record.extra)
            extra_str = f" | {extra_mascarado}"

        correlacao_ctx = obter_correlacao_id()
        correlacao_str = f" [{correlacao_ctx}]" if correlacao_ctx else ""

        return f"{cor}{timestamp} [{nivel}]{correlacao_str} {nome} - {mensagem}{extra_str}{reset}"


# ============================================================================
# CONFIGURAÇÃO GLOBAL
# ============================================================================

_logging_configurado = False


def resetar_configuracao_logging() -> None:
    """Reseta a flag de logging para permitir reconfigurações em testes."""
    global _logging_configurado
    _logging_configurado = False


def configurar_logging(
    config: ConfiguracaoLogging,
    ambiente: Ambiente = Ambiente.DESENVOLVIMENTO,
) -> None:
    """
    Configura o logging global do sistema.

    Args:
        config: Configuração de logging (nível, formato, destino)
        ambiente: Ambiente atual
    """
    global _logging_configurado

    if _logging_configurado:
        return

    # Converter nível
    nivel_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    nivel = nivel_map.get(config.nivel.upper(), logging.INFO)

    # Criar handler
    if config.destino == "arquivo" and getattr(config, "arquivo_log", None):
        handler = logging.FileHandler(config.arquivo_log, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)

    # Escolher formatador
    if config.formato == "json":
        formatador = FormatadorJSON(ambiente)
    else:
        formatador = FormatadorTexto()

    handler.setFormatter(formatador)

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(nivel)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    _logging_configurado = True


def obter_logger(nome: str) -> logging.Logger:
    """
    Obtém um logger com namespace.

    Args:
        nome: Nome do módulo (ex: "dominio.servicos")

    Returns:
        Logger configurado
    """
    if nome.startswith("mestre_ia."):
        return logging.getLogger(nome)
    return logging.getLogger(f"mestre_ia.{nome}")


class LoggerComContexto:
    """
    Wrapper que adiciona contexto fixo a todos os logs.
    """

    def __init__(self, logger: logging.Logger, **contexto: Any):
        self._logger = logger
        self._contexto = contexto

    def _log(self, nivel: int, mensagem: str, **extra: Any) -> None:
        contexto_completo = {**self._contexto, **extra}
        self._logger.log(nivel, mensagem, extra={"extra": contexto_completo})

    def debug(self, mensagem: str, **extra: Any) -> None:
        self._log(logging.DEBUG, mensagem, **extra)

    def info(self, mensagem: str, **extra: Any) -> None:
        self._log(logging.INFO, mensagem, **extra)

    def warning(self, mensagem: str, **extra: Any) -> None:
        self._log(logging.WARNING, mensagem, **extra)

    def error(self, mensagem: str, **extra: Any) -> None:
        self._log(logging.ERROR, mensagem, **extra)

    def critical(self, mensagem: str, **extra: Any) -> None:
        self._log(logging.CRITICAL, mensagem, **extra)

    def com_contexto(self, **contexto_adicional: Any) -> "LoggerComContexto":
        """Cria um novo logger com contexto adicional."""
        contexto_completo = {**self._contexto, **contexto_adicional}
        return LoggerComContexto(self._logger, **contexto_completo)
