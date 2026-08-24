"""
Testes unitários para MemoriaSemantica.
"""

import pytest
from mestre_ia.memoria.embeddings import GeradorEmbeddings
from mestre_ia.memoria.vetorial import ArmazenamentoVetorial
from mestre_ia.memoria.semantica import MemoriaSemantica


class TestMemoriaSemantica:
    """Testes da MemoriaSemantica."""

    @pytest.fixture
    def gerador(self):
        """Gerador fake para testes."""
        return GeradorEmbeddings(modo_fake=True)

    @pytest.fixture
    def armazenamento(self, gerador):
        """Armazenamento compatível com o gerador."""
        return ArmazenamentoVetorial(
            dimensao=gerador.dimensao,
            threshold=0.0,
        )

    @pytest.fixture
    def memoria(self, gerador, armazenamento):
        """Memória semântica completa."""
        return MemoriaSemantica(gerador, armazenamento)

    def test_inicializacao(self, memoria, gerador, armazenamento):
        """Deve inicializar corretamente."""
        assert memoria.gerador == gerador
        assert memoria.armazenamento == armazenamento
        assert memoria.armazenamento.total_documentos == 0

    def test_inicializacao_dimensao_incompativel(self):
        """Deve rejeitar dimensões incompatíveis."""
        gerador = GeradorEmbeddings(modo_fake=True)
        armaz = ArmazenamentoVetorial(dimensao=999, threshold=0.5)
        with pytest.raises(ValueError, match="Dimensão incompatível"):
            MemoriaSemantica(gerador, armaz)

    def test_usando_modelo_real_fake(self, memoria):
        """Modo fake deve reportar usando_modelo_real=False."""
        assert memoria.usando_modelo_real is False

    @pytest.mark.asyncio
    async def test_armazenar(self, memoria):
        """Deve armazenar documento com sucesso."""
        doc_id = await memoria.armazenar("Informação importante")
        assert doc_id is not None
        assert memoria.armazenamento.total_documentos == 1

    @pytest.mark.asyncio
    async def test_armazenar_multiplos(self, memoria):
        """Deve armazenar múltiplos documentos."""
        await memoria.armazenar("Doc 1")
        await memoria.armazenar("Doc 2")
        await memoria.armazenar("Doc 3")
        assert memoria.armazenamento.total_documentos == 3

    @pytest.mark.asyncio
    async def test_armazenar_com_metadados(self, memoria):
        """Deve preservar metadados."""
        doc_id = await memoria.armazenar("Texto", metadados={"fonte": "teste"})
        doc = memoria.armazenamento.obter(doc_id)
        assert doc.metadados["fonte"] == "teste"

    @pytest.mark.asyncio
    async def test_armazenar_texto_vazio(self, memoria):
        """Deve rejeitar texto vazio."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            await memoria.armazenar("")

    @pytest.mark.asyncio
    async def test_buscar_documentos(self, memoria):
        """Deve encontrar documentos similares."""
        await memoria.armazenar("Python e uma linguagem de programacao")
        await memoria.armazenar("Java e uma linguagem de programacao")
        await memoria.armazenar("O ceu e azul")

        resultados = await memoria.buscar_documentos(
            "linguagens de programacao", top_k=2
        )
        assert len(resultados) == 2
        assert all(hasattr(doc, 'texto') for doc in resultados)

    @pytest.mark.asyncio
    async def test_buscar_contexto(self, memoria):
        """Deve retornar contexto formatado."""
        await memoria.armazenar("Python e uma linguagem popular")
        await memoria.armazenar("Java e usada em aplicacoes enterprise")

        contexto = await memoria.buscar_contexto("programacao", top_k=2)
        assert contexto is not None
        assert "Python" in contexto or "Java" in contexto

    @pytest.mark.asyncio
    async def test_buscar_contexto_sem_resultados(self, memoria):
        """Deve retornar None quando não há resultados."""
        contexto = await memoria.buscar_contexto("consulta sem correspondencia")
        assert contexto is None

    @pytest.mark.asyncio
    async def test_limpar(self, memoria):
        """Deve limpar todos os documentos."""
        await memoria.armazenar("Doc 1")
        await memoria.armazenar("Doc 2")
        await memoria.limpar()
        assert memoria.armazenamento.total_documentos == 0