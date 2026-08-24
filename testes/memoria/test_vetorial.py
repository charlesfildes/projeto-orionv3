"""
Testes unitários para ArmazenamentoVetorial.
"""

import pytest
from mestre_ia.memoria.vetorial import ArmazenamentoVetorial, DocumentoVetorial


class TestArmazenamentoVetorial:
    """Testes do ArmazenamentoVetorial."""

    @pytest.fixture
    def armazenamento(self):
        """Armazenamento com dimensão 4 para testes."""
        return ArmazenamentoVetorial(dimensao=4, threshold=0.5)

    @pytest.fixture
    def embedding_base(self):
        """Embedding de exemplo."""
        return [1.0, 0.0, 0.0, 0.0]

    def test_inicializacao_padrao(self):
        """Deve inicializar com parâmetros corretos."""
        armaz = ArmazenamentoVetorial()
        assert armaz.dimensao == 384
        assert armaz.total_documentos == 0

    def test_adicionar_documento(self, armazenamento, embedding_base):
        """Deve adicionar documento com sucesso."""
        doc_id = armazenamento.adicionar("texto de exemplo", embedding_base)
        assert doc_id is not None
        assert armazenamento.total_documentos == 1

    def test_adicionar_com_id_customizado_e_metadados(self, armazenamento, embedding_base):
        """Deve adicionar documento informando ID customizado e metadados."""
        doc_id = armazenamento.adicionar(
            "texto custom", embedding_base, metadados={"fonte": "livro"}, doc_id="custom-123"
        )
        assert doc_id == "custom-123"
        assert armazenamento.total_documentos == 1

    def test_adicionar_dimensao_incompativel(self, armazenamento):
        """Deve rejeitar embedding com dimensão errada."""
        with pytest.raises(ValueError, match="Dimensão do embedding \\(2\\) incompatível com o armazenamento \\(4\\)"):
            armazenamento.adicionar("texto", [1.0, 2.0])

    def test_buscar_similares_resultado(self, armazenamento, embedding_base):
        """Deve encontrar documento similar ordenado e respeitando top_k."""
        armazenamento.adicionar("texto relevante", embedding_base)
        armazenamento.adicionar("texto muito relevante", [0.9, 0.1, 0.0, 0.0])
        resultados = armazenamento.buscar_similares(embedding_base, top_k=1)
        assert len(resultados) == 1
        assert resultados[0].texto == "texto relevante"
        assert resultados[0].similaridade == 1.0

    def test_buscar_similares_abaixo_threshold(self, armazenamento):
        """Não deve retornar documentos abaixo do threshold."""
        armazenamento.adicionar("texto X", [1.0, 0.0, 0.0, 0.0])
        # Vetor ortogonal -> similaridade 0.0 (abaixo do threshold 0.5)
        resultados = armazenamento.buscar_similares([0.0, 1.0, 0.0, 0.0])
        assert len(resultados) == 0

    def test_buscar_similares_vazio_ou_sem_documentos(self, armazenamento, embedding_base):
        """Deve retornar lista vazia se não há consulta ou documentos."""
        assert armazenamento.buscar_similares([]) == []
        assert armazenamento.buscar_similares(embedding_base) == []

    def test_limpar(self, armazenamento, embedding_base):
        """Deve remover todos os documentos."""
        armazenamento.adicionar("A", embedding_base)
        armazenamento.adicionar("B", embedding_base)
        armazenamento.limpar()
        assert armazenamento.total_documentos == 0

    def test_similaridade_cosseno_casos_borda(self, armazenamento):
        """Deve cobrir validações internas da similaridade de cosseno."""
        # Vetores de tamanhos diferentes
        assert armazenamento._similaridade_cosseno([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0
        # Vetores com norma zero
        assert armazenamento._similaridade_cosseno([0.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]) == 0.0


class TestDocumentoVetorial:
    """Testes da dataclass DocumentoVetorial."""

    def test_criacao_documento_vetorial(self):
        """Verifica inicialização padrão da dataclass DocumentoVetorial."""
        doc = DocumentoVetorial(texto="exemplo", embedding=[0.1, 0.2])
        assert doc.texto == "exemplo"
        assert doc.embedding == [0.1, 0.2]
        assert doc.doc_id is not None
        assert doc.metadados is None
        assert doc.similaridade is None
