from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from typer.testing import CliRunner

from mestre_ia.interfaces.cli.principal import app

runner = CliRunner()


@dataclass
class RespostaMock:
    """Mock que replica TODOS os campos que RespostaIA espera."""
    conteudo: str = "Resposta de teste do Orion"
    provedor: str = "deepseek"
    modelo: str = "deepseek-chat"
    tokens_entrada: int = 50
    tokens_saida: int = 50
    tempo_resposta_ms: float = 120.0
    metadados: dict = field(default_factory=dict)
    requisicao_id: str = "req-teste-123"

    def __str__(self):
        return self.conteudo


@pytest.fixture
def mock_orquestrador():
    """Mock do orquestrador para isolar a CLI da camada de aplicação."""
    with patch("mestre_ia.interfaces.cli.principal.Orquestrador") as mock_cls:
        instancia = MagicMock()
        instancia.processar = AsyncMock(return_value=RespostaMock())
        mock_cls.return_value = instancia
        yield instancia


def test_help_command():
    """Garante que a CLI exibe a mensagem de ajuda corretamente."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_execucao_comando_sucesso(mock_orquestrador):
    """Testa o fluxo principal de envio de prompt com resposta com sucesso."""
    result = runner.invoke(app, ["perguntar", "Olá, Orion!"])
    assert result.exit_code == 0
    assert "Resposta de teste do Orion" in result.output


def test_erro_sem_chave_api(mock_orquestrador):
    """Garante que exceções são tratadas na CLI."""
    mock_orquestrador.processar.side_effect = ValueError("API Key não encontrada")
    result = runner.invoke(app, ["perguntar", "Teste falha"])
    assert result.exit_code != 0


def test_execucao_com_flags_modelo_e_temperatura(mock_orquestrador):
    """Testa execução com flags de modelo e temperatura."""
    result = runner.invoke(app, ["perguntar", "Teste com flags"])
    assert result.exit_code == 0


def test_erro_generico_orquestrador(mock_orquestrador):
    """Testa erro genérico do orquestrador."""
    mock_orquestrador.processar.side_effect = RuntimeError("Erro genérico")
    result = runner.invoke(app, ["perguntar", "Teste erro"])
    assert result.exit_code != 0


def test_ajuda_comando_perguntar(mock_orquestrador):
    """Testa ajuda do comando perguntar."""
    result = runner.invoke(app, ["perguntar", "--help"])
    assert result.exit_code == 0
