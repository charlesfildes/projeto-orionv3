"""
Testes unitários para o sistema de configuração.
"""

import os
import pytest
from unittest.mock import patch
from pathlib import Path

from mestre_ia.core.configuracao import (
    Ambiente,
    Configuracao,
    ConfiguracaoIA,
    ConfiguracaoLogging,
    ConfiguracaoMemoria,
    ConfiguracaoQuantum,
    ConfiguracaoSeguranca,
)


class TestAmbiente:
    """Testes para detecção de ambiente."""

    def test_desenvolvimento_default(self):
        """Sem variável definida, deve retornar DESENVOLVIMENTO."""
        with patch.dict(os.environ, {}, clear=True):
            ambiente = Ambiente.detectar()
            assert ambiente == Ambiente.DESENVOLVIMENTO

    def test_producao_por_variavel(self):
        """Deve detectar PRODUCAO pela variável."""
        with patch.dict(os.environ, {"MESTRE_IA_AMBIENTE": "prod"}):
            ambiente = Ambiente.detectar()
            assert ambiente == Ambiente.PRODUCAO

    def test_valor_invalido_retorna_dev(self):
        """Valor não reconhecido deve retornar DESENVOLVIMENTO."""
        with patch.dict(os.environ, {"MESTRE_IA_AMBIENTE": "invalido"}):
            ambiente = Ambiente.detectar()
            assert ambiente == Ambiente.DESENVOLVIMENTO


class TestConfiguracaoLogging:
    """Testes da ConfiguracaoLogging."""

    def test_valores_padrao(self):
        """Deve ter valores padrão corretos."""
        config = ConfiguracaoLogging()
        assert config.nivel == "INFO"
        assert config.formato == "json"
        assert config.destino == "stdout"

    def test_nivel_invalido(self):
        """Deve rejeitar nível inválido."""
        with pytest.raises(ValueError, match="Nível de log inválido"):
            ConfiguracaoLogging(nivel="INVALIDO")

    def test_formato_invalido(self):
        """Deve rejeitar formato inválido."""
        with pytest.raises(ValueError, match="Formato de log inválido"):
            ConfiguracaoLogging(formato="xml")


class TestConfiguracaoIA:
    """Testes da ConfiguracaoIA."""

    def test_valores_padrao(self):
        """Deve ter valores padrão corretos."""
        config = ConfiguracaoIA()
        assert config.provedor_padrao == "deepseek"
        assert config.timeout_ms == 30000
        assert config.max_retries == 3
        assert config.provedores == {}

    def test_timeout_invalido(self):
        """Deve rejeitar timeout <= 0."""
        with pytest.raises(ValueError, match="timeout_ms"):
            ConfiguracaoIA(timeout_ms=0)

    def test_max_retries_negativo(self):
        """Deve rejeitar max_retries negativo."""
        with pytest.raises(ValueError, match="max_retries"):
            ConfiguracaoIA(max_retries=-1)


class TestConfiguracaoMemoria:
    """Testes da ConfiguracaoMemoria."""

    def test_valores_padrao(self):
        """Deve ter valores padrão corretos."""
        config = ConfiguracaoMemoria()
        assert config.tipo_vetorial == "chromadb"
        assert config.dimensao_embeddings == 1536
        assert config.similaridade_threshold == 0.7

    def test_threshold_invalido(self):
        """Deve rejeitar threshold fora do intervalo."""
        with pytest.raises(ValueError):
            ConfiguracaoMemoria(similaridade_threshold=1.5)
        with pytest.raises(ValueError):
            ConfiguracaoMemoria(similaridade_threshold=-0.1)

    def test_dimensao_invalida(self):
        """Deve rejeitar dimensão <= 0."""
        with pytest.raises(ValueError):
            ConfiguracaoMemoria(dimensao_embeddings=0)


class TestConfiguracaoQuantum:
    """Testes da ConfiguracaoQuantum."""

    def test_valores_padrao(self):
        """Deve ter valores padrão corretos."""
        config = ConfiguracaoQuantum()
        assert config.backend_padrao == "simulador"
        assert config.shots_padrao == 1024
        assert config.ibm_token is None

    def test_shots_invalido(self):
        """Deve rejeitar shots <= 0."""
        with pytest.raises(ValueError):
            ConfiguracaoQuantum(shots_padrao=0)


class TestConfiguracaoSeguranca:
    """Testes da ConfiguracaoSeguranca."""

    def test_valores_padrao(self):
        """Deve ter valores padrão corretos."""
        config = ConfiguracaoSeguranca()
        assert config.jwt_secret is None
        assert config.jwt_algoritmo == "HS256"
        assert config.mfa_habilitado is False

    def test_jwt_expiracao_invalida(self):
        """Deve rejeitar expiração <= 0."""
        with pytest.raises(ValueError):
            ConfiguracaoSeguranca(jwt_expiracao_minutos=0)


class TestConfiguracao:
    """Testes da Configuracao raiz."""

    def test_valores_padrao(self):
        """Deve criar com valores padrão."""
        config = Configuracao()
        assert config.ambiente == Ambiente.DESENVOLVIMENTO
        assert config.debug is False
        assert config.ia.provedor_padrao == "deepseek"
        assert config.memoria.tipo_vetorial == "chromadb"

    def test_para_dict_seguro_oculta_sensiveis(self):
        """Deve omitir tokens e secrets na serialização."""
        ia_config = ConfiguracaoIA(
            provedores={
                "deepseek": {
                    "api_key": "sk-secreta-123",
                    "modelo_padrao": "deepseek-chat",
                }
            }
        )
        config = Configuracao(ia=ia_config)
        seguro = config.para_dict_seguro()

        # API key não deve aparecer no dict seguro
        assert "sk-secreta" not in str(seguro)
        assert "api_key" not in str(seguro)

    def test_para_dict_seguro_contem_seguranca_sem_jwt(self):
        """Deve incluir informações de segurança sem jwt_secret."""
        seguranca_config = ConfiguracaoSeguranca(jwt_secret="segredo")
        config = Configuracao(seguranca=seguranca_config)
        seguro = config.para_dict_seguro()

        assert "jwt_algoritmo" in seguro["seguranca"]
        assert "segredo" not in str(seguro)

    def test_carregar_de_ambiente(self):
        """Deve carregar configurações de variáveis de ambiente."""
        with patch.dict(os.environ, {
            "MESTRE_IA_DEBUG": "true",
            "MESTRE_IA_IA_TIMEOUT_MS": "60000",
        }):
            config = Configuracao.carregar()
            assert config.debug is True
            assert config.ia.timeout_ms == 60000

    def test_carregar_deepseek_api_key(self):
        """Deve capturar DEEPSEEK_API_KEY para config.ia.provedores."""
        with patch.dict(os.environ, {
            "DEEPSEEK_API_KEY": "sk-teste-abc",
            "DEEPSEEK_MODELO_PADRAO": "deepseek-chat",
        }):
            config = Configuracao.carregar()
            assert "deepseek" in config.ia.provedores
            assert config.ia.provedores["deepseek"]["api_key"] == "sk-teste-abc"


class TestCarregarDotenv:
    """Testes de carregamento de arquivo .env."""

    def test_carregar_dotenv_basico(self, tmp_path):
        """Deve carregar variáveis de um arquivo .env como strings."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MESTRE_IA_DEBUG=true\n"
            "DEEPSEEK_API_KEY=sk-teste-dotenv\n"
        )

        config_dict = Configuracao._carregar_dotenv(env_file)

        assert config_dict.get("debug") == "true"
        assert config_dict.get("deepseek_api_key") == "sk-teste-dotenv"

    def test_carregar_dotenv_ignora_comentarios(self, tmp_path):
        """Deve ignorar linhas de comentário."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# Comentario\n"
            "MESTRE_IA_DEBUG=true\n"
        )

        config_dict = Configuracao._carregar_dotenv(env_file)

        assert "comentario" not in config_dict
        assert config_dict.get("debug") == "true"


class TestNormalizarChaves:
    """Testes de normalização de chaves."""

    def test_remove_prefixo_mestre_ia(self):
        """Deve remover o prefixo MESTRE_IA_."""
        raw = {
            "MESTRE_IA_DEBUG": "true",
            "OUTRA_CHAVE": "valor",
        }
        resultado = Configuracao._normalizar_chaves(raw)

        assert "debug" in resultado
        assert "MESTRE_IA_DEBUG" not in resultado
        assert "outra_chave" in resultado

    def test_chaves_sem_prefixo_preservadas(self):
        """Chaves sem prefixo devem ser preservadas em minúsculas."""
        raw = {"DEEPSEEK_API_KEY": "sk-teste"}
        resultado = Configuracao._normalizar_chaves(raw)

        assert resultado["deepseek_api_key"] == "sk-teste"
