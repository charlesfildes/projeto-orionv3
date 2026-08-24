"""
Gerador de Embeddings — Projeto Orion.

Utiliza sentence-transformers (dependência opcional [memoria])
com modelo all-MiniLM-L6-v2 (384 dimensões).

Suporta também um modo fake para testes sem download de modelo.
"""

from typing import List, Optional


class GeradorEmbeddings:
    """
    Gera embeddings vetoriais a partir de texto.

    Modo real: usa sentence-transformers com all-MiniLM-L6-v2
    Modo fake: gera vetores baseados em hash para testes

    Uso:
        gerador = GeradorEmbeddings()
        embedding = gerador.gerar("texto de exemplo")
        print(gerador.dimensao)  # 384
    """

    def __init__(
        self,
        modelo_nome: str = "all-MiniLM-L6-v2",
        modo_fake: bool = False,
    ):
        """
        Inicializa o gerador de embeddings.

        Args:
            modelo_nome: Nome do modelo sentence-transformers
            modo_fake: Se True, gera vetores hash (para testes)
        """
        self._modo_fake = modo_fake
        self._modelo_nome = modelo_nome
        self._modelo = None
        self._dimensao: Optional[int] = None

        if not modo_fake:
            self._inicializar_modelo()

    def _inicializar_modelo(self) -> None:
        """Inicializa o modelo sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            self._modelo = SentenceTransformer(self._modelo_nome)
            self._dimensao = self._modelo.get_sentence_embedding_dimension()
        except ImportError:
            raise ImportError(
                "sentence-transformers não está instalado. "
                "Instale com: pip install mestre-ia[memoria] "
                "ou use modo_fake=True para testes."
            )

    @property
    def dimensao(self) -> int:
        """
        Dimensão real dos embeddings gerados.

        Para all-MiniLM-L6-v2: 384
        Para OpenAI text-embedding-3-small: 1536
        """
        if self._dimensao is not None:
            return self._dimensao
        return 384

    @property
    def modelo_nome(self) -> str:
        """Nome do modelo em uso."""
        return self._modelo_nome

    @property
    def modo_fake(self) -> bool:
        """Se está em modo fake (sem modelo real)."""
        return self._modo_fake

    def gerar(self, texto: str) -> List[float]:
        """
        Gera embedding para o texto fornecido.

        Args:
            texto: Texto para gerar embedding

        Returns:
            Lista de floats representando o embedding

        Raises:
            ValueError: Se o texto for vazio
        """
        if not texto or not texto.strip():
            raise ValueError("Texto não pode ser vazio para gerar embedding")

        if self._modo_fake:
            import hashlib
            hash_bytes = hashlib.sha256(texto.encode()).digest()
            dimensao = self.dimensao
            embedding = []
            for i in range(dimensao):
                byte_val = hash_bytes[i % len(hash_bytes)]
                embedding.append((byte_val / 255.0) * 2.0 - 1.0)
            return embedding

        if self._modelo is None:
            raise RuntimeError("Modelo não inicializado")

        embedding = self._modelo.encode(texto)
        return embedding.tolist()

    def gerar_lote(self, textos: List[str]) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos.

        Args:
            textos: Lista de textos

        Returns:
            Lista de embeddings
        """
        return [self.gerar(texto) for texto in textos]
