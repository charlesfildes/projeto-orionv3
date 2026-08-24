"""
Armazenamento vetorial em memória para documentos e embeddings.
"""

from dataclasses import dataclass, field
import uuid
from typing import Dict, List, Optional
import numpy as np


@dataclass
class DocumentoVetorial:
    texto: str
    embedding: List[float]
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadados: Optional[dict] = None
    similaridade: Optional[float] = None


class ArmazenamentoVetorial:
    """Armazenamento e busca de documentos por similaridade de vetores."""

    def __init__(self, dimensao: int = 384, threshold: float = 0.5):
        self.dimensao = dimensao
        self.threshold = threshold
        self._documentos: Dict[str, DocumentoVetorial] = {}

    @property
    def total_documentos(self) -> int:
        """Retorna o número total de documentos armazenados."""
        return len(self._documentos)

    def _similaridade_cosseno(self, v1: List[float], v2: List[float]) -> float:
        """Calcula a similaridade de cosseno entre dois vetores."""
        if len(v1) != len(v2):
            return 0.0
        vec1 = np.array(v1)
        vec2 = np.array(v2)
        norma1 = np.linalg.norm(vec1)
        norma2 = np.linalg.norm(vec2)
        if norma1 == 0 or norma2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norma1 * norma2))

    def adicionar(
        self,
        texto: str,
        embedding: List[float],
        doc_id: Optional[str] = None,
        metadados: Optional[dict] = None,
    ) -> str:
        if len(embedding) != self.dimensao:
            raise ValueError(
                f"Dimensão do embedding ({len(embedding)}) incompatível com o armazenamento ({self.dimensao})"
            )

        id_final = doc_id or str(uuid.uuid4())
        doc = DocumentoVetorial(
            texto=texto,
            embedding=embedding,
            doc_id=id_final,
            metadados=metadados,
        )
        self._documentos[id_final] = doc
        return id_final

    def obter(self, doc_id: str) -> Optional[DocumentoVetorial]:
        """Retorna um documento armazenado pelo seu ID."""
        return self._documentos.get(doc_id)

    def buscar_similares(
        self,
        embedding_consulta: List[float],
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[DocumentoVetorial]:
        if not self._documentos or len(embedding_consulta) != self.dimensao:
            return []

        limite = threshold if threshold is not None else self.threshold

        resultados = []
        for doc in self._documentos.values():
            similaridade = self._similaridade_cosseno(embedding_consulta, doc.embedding)
            if limite is None or similaridade >= limite:
                doc_copia = DocumentoVetorial(
                    texto=doc.texto,
                    embedding=doc.embedding,
                    doc_id=doc.doc_id,
                    metadados=doc.metadados,
                    similaridade=similaridade,
                )
                resultados.append(doc_copia)

        resultados.sort(key=lambda x: x.similaridade if x.similaridade is not None else -1.0, reverse=True)
        return resultados[:top_k]

    def limpar(self):
        self._documentos.clear()