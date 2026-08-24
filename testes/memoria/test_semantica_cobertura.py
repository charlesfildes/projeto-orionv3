"""
Testes de cobertura para MemoriaSemantica.
API real: metodos async (armazenar, buscar_contexto, buscar_documentos, limpar)
"""

import pytest
from mestre_ia.memoria.embeddings import GeradorEmbeddings
from mestre_ia.memoria.vetorial import ArmazenamentoVetorial
from mestre_ia.memoria.semantica import MemoriaSemantica


@pytest.fixture
def gerador():
    """Gerador fake."""
    return GeradorEmbeddings(modo_fake=True)


@pytest.fixture
def armazenamento(gerador):
    """Armazenamento com threshold=0.0."""
    return ArmazenamentoVetorial(
        dimensao=gerador.dimensao,
        threshold=0.0,
    )


@pytest.fixture
def memoria(gerador, armazenamento):
    """Memória semântica completa."""
    return MemoriaSemantica(gerador, armazenamento)


class TestInicializacao:
    """Testes de inicialização."""

    def test_dimensoes_incompativeis_lanca_erro(self):
        """Deve lançar ValueError para dimensões incompatíveis."""
        gerador = GeradorEmbeddings(modo_fake=True)
        armaz = ArmazenamentoVetorial(dimensao=999, threshold=0.5)

        with pytest.raises(ValueError, match="Dimensão incompatível"):
            MemoriaSemantica(gerador, armaz)

    def test_inicializacao_valida(self, memoria):
        """Deve inicializar corretamente."""
        assert memoria.armazenamento.total_documentos == 0
        assert memoria.usando_modelo_real is False


class TestArmazenar:
    """Testes do método armazenar (async)."""

    @pytest.mark.asyncio
    async def test_armazenar_texto_vazio_lanca_erro(self, memoria):
        """Deve lançar ValueError para texto vazio."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            await memoria.armazenar("")

    @pytest.mark.asyncio
    async def test_armazenar_texto_none_lanca_erro(self, memoria):
        """Deve lançar ValueError para None."""
        with pytest.raises((ValueError, AttributeError)):
            await memoria.armazenar(None)

    @pytest.mark.asyncio
    async def test_armazenar_documento(self, memoria):
        """Deve armazenar documento com sucesso."""
        doc_id = await memoria.armazenar("Documento de teste")
        assert doc_id is not None
        assert memoria.armazenamento.total_documentos == 1


class TestBuscarDocumentos:
    """Testes do método buscar_documentos (async)."""

    @pytest.mark.asyncio
    async def test_buscar_documentos_consulta_vazia(self, memoria):
        """Deve retornar lista vazia para consulta vazia."""
        resultados = await memoria.buscar_documentos("")
        assert resultados == []

    @pytest.mark.asyncio
    async def test_buscar_documentos_retorna_resultados(self, memoria):
        """Deve retornar documentos armazenados."""
        await memoria.armazenar("Documento sobre Python")
        await memoria.armazenar("Documento sobre Java")
        await memoria.armazenar("Documento sobre medicina")

        resultados = await memoria.buscar_documentos("programacao", top_k=3)

        assert len(resultados) == 3
        for doc in resultados:
            assert doc.texto is not None

    @pytest.mark.asyncio
    async def test_buscar_documentos_top_k(self, memoria):
        """Deve respeitar top_k."""
        for i in range(5):
            await memoria.armazenar(f"Documento {i}")

        resultados = await memoria.buscar_documentos("documento", top_k=2)
        assert len(resultados) == 2


class TestBuscarContexto:
    """Testes do método buscar_contexto (async)."""

    @pytest.mark.asyncio
    async def test_buscar_contexto_retorna_textos(self, memoria):
        """Deve retornar contexto concatenado."""
        await memoria.armazenar("Primeira informação")
        await memoria.armazenar("Segunda informação")

        contexto = await memoria.buscar_contexto("informação", top_k=2)

        assert contexto is not None
        assert "Primeira informação" in contexto
        assert "Segunda informação" in contexto

    @pytest.mark.asyncio
    async def test_buscar_contexto_sem_resultados(self, memoria):
        """Deve retornar None sem resultados."""
        contexto = await memoria.buscar_contexto("nada")
        assert contexto is None


class TestEstatisticas:
    """Testes de estatísticas."""

    @pytest.mark.asyncio
    async def test_total_documentos(self, memoria):
        """Deve contar documentos corretamente."""
        for i in range(42):
            await memoria.armazenar(f"Doc {i}")
        assert memoria.armazenamento.total_documentos == 42

    @pytest.mark.asyncio
    async def test_limpar_memoria(self, memoria):
        """Deve limpar todos os documentos."""
        await memoria.armazenar("Doc 1")
        await memoria.armazenar("Doc 2")

        await memoria.limpar()

        assert memoria.armazenamento.total_documentos == 0
