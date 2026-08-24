"""
Testes unitários completos para GeradorEmbeddings (Modo Fake + Modo Real com Mocks).
"""

import sys
from unittest.mock import MagicMock, patch
import pytest

from mestre_ia.memoria.embeddings import GeradorEmbeddings


class TestGeradorEmbeddingsFake:
    """Testes com modo fake (sem dependência externa)."""

    @pytest.fixture
    def gerador(self):
        """Gerador em modo fake."""
        return GeradorEmbeddings(modo_fake=True)

    def test_inicializacao_fake(self, gerador):
        """Deve inicializar em modo fake."""
        assert gerador.modo_fake is True
        assert gerador.dimensao == 384
        assert gerador.modelo_nome == "all-MiniLM-L6-v2"

    def test_gerar_embedding_fake(self, gerador):
        """Deve gerar embedding de dimensão correta."""
        embedding = gerador.gerar("texto de teste")
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_gerar_embedding_deterministico(self, gerador):
        """Mesmo texto deve gerar mesmo embedding."""
        e1 = gerador.gerar("teste")
        e2 = gerador.gerar("teste")
        assert e1 == e2

    def test_gerar_embedding_textos_diferentes(self, gerador):
        """Textos diferentes devem gerar embeddings diferentes."""
        e1 = gerador.gerar("texto A")
        e2 = gerador.gerar("texto B")
        assert e1 != e2

    def test_texto_vazio_lanca_erro(self, gerador):
        """Deve rejeitar texto vazio."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            gerador.gerar("")

    def test_texto_apenas_espacos_lanca_erro(self, gerador):
        """Deve rejeitar texto apenas com espaços."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            gerador.gerar("   ")

    def test_gerar_lote(self, gerador):
        """Deve gerar embeddings para múltiplos textos."""
        textos = ["texto 1", "texto 2", "texto 3"]
        embeddings = gerador.gerar_lote(textos)
        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 384


class TestGeradorEmbeddingsModoReal:
    """Testes com mocks para o modo real com sentence-transformers."""

    def test_inicializacao_e_geracao_modo_real(self):
        """Deve inicializar o modelo e converter o array retornado para lista."""
        mock_model_instance = MagicMock()
        mock_model_instance.get_sentence_embedding_dimension.return_value = 384
        
        mock_array = MagicMock()
        mock_array.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model_instance.encode.return_value = mock_array

        mock_sentence_tf_class = MagicMock(return_value=mock_model_instance)

        with patch.dict(sys.modules, {"sentence_transformers": MagicMock(SentenceTransformer=mock_sentence_tf_class)}):
            gerador = GeradorEmbeddings(modo_fake=False)
            assert gerador.modo_fake is False
            assert gerador.dimensao == 384

            res = gerador.gerar("teste modo real")
            assert res == [0.1, 0.2, 0.3]
            mock_model_instance.encode.assert_called_once_with("teste modo real")

    def test_import_error_quando_dependencia_ausente(self):
        """Deve lançar ImportError amigável se sentence-transformers não estiver instalado."""
        with patch.dict(sys.modules, {"sentence_transformers": None}):
            with pytest.raises(ImportError, match="sentence-transformers não está instalado"):
                GeradorEmbeddings(modo_fake=False)

    def test_runtime_error_se_modelo_nao_inicializado(self):
        """Deve lançar RuntimeError se _modelo for None ao chamar gerar em modo real."""
        gerador = GeradorEmbeddings(modo_fake=True)
        # Força o modo fake para False sem carregar modelo
        gerador._modo_fake = False
        gerador._modelo = None

        with pytest.raises(RuntimeError, match="Modelo não inicializado"):
            gerador.gerar("teste erro")
