"""
Módulo de Memória Semântica da IA Mestre.
"""

import logging
from typing import Any, Dict, List, Optional

from mestre_ia.memoria.embeddings import GeradorEmbeddings
from mestre_ia.memoria.vetorial import ArmazenamentoVetorial, DocumentoVetorial

logger = logging.getLogger(__name__)


class MemoriaSemantica:
    """Gerencia a memória semântica baseada em vetores e embeddings."""

    def __init__(
        self,
        gerador: GeradorEmbeddings,
        armazenamento: ArmazenamentoVetorial,
    ):
        if gerador.dimensao != armazenamento.dimensao:
            raise ValueError(
                f"Dimensão incompatível: gerador ({gerador.dimensao}) "
                f"e armazenamento ({armazenamento.dimensao})."
            )
        self._gerador = gerador
        self._armazenamento = armazenamento

    @property
    def gerador(self) -> GeradorEmbeddings:
        return self._gerador

    @property
    def armazenamento(self) -> ArmazenamentoVetorial:
        return self._armazenamento

    @property
    def usando_modelo_real(self) -> bool:
        return getattr(self._gerador, "usando_modelo_real", False)

    @property
    def total_documentos(self) -> int:
        docs = getattr(
            self._armazenamento,
            "documentos",
            getattr(self._armazenamento, "_documentos", []),
        )
        return len(docs)

    async def armazenar(
        self,
        texto: str,
        metadados: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        if not texto or not texto.strip():
            raise ValueError("Texto não pode ser vazio")

        embedding = self._gerador.gerar(texto)
        doc = self._armazenamento.adicionar(
            texto=texto,
            embedding=embedding,
            metadados=metadados,
            doc_id=doc_id,
        )

        id_retornado = doc.doc_id if hasattr(doc, "doc_id") else doc

        logger.info(
            "Documento armazenado na memória semântica",
            extra={
                "contexto": {
                    "doc_id": id_retornado,
                    "total_documentos": self.total_documentos,
                }
            },
        )
        return id_retornado

    async def armazenar_multiplos(
        self,
        textos: List[str],
        metadados_lista: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        ids = []
        for i, texto in enumerate(textos):
            meta = metadados_lista[i] if metadados_lista and i < len(metadados_lista) else None
            doc_id = await self.armazenar(texto, metadados=meta)
            ids.append(doc_id)
        return ids

    async def buscar_documentos(
        self,
        consulta: str,
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[DocumentoVetorial]:
        if not consulta or not consulta.strip():
            logger.debug("Consulta vazia, retornando lista vazia")
            return []

        embedding_consulta = self._gerador.gerar(consulta)

        # Se threshold não for explicitamente fornecido, passamos -1.0 para desativar 
        # qualquer corte mínimo de similaridade do ArmazenamentoVetorial
        kwargs = {"top_k": top_k}
        if threshold is not None:
            kwargs["threshold"] = threshold
        else:
            kwargs["threshold"] = -1.0

        documentos = self._armazenamento.buscar_similares(
            embedding_consulta,
            **kwargs,
        )

        logger.debug(
            "Busca semântica concluída",
            extra={"resultados": len(documentos), "top_k": top_k},
        )

        return documentos

    async def buscar_contexto(
        self,
        consulta: str,
        top_k: int = 3,
        threshold: Optional[float] = None,
    ) -> Optional[str]:
        docs = await self.buscar_documentos(consulta, top_k=top_k, threshold=threshold)
        if not docs:
            return None
        return "\n\n".join([doc.texto for doc in docs])

    async def limpar(self) -> None:
        """Remove todos os documentos da memória semântica."""
        self._armazenamento.limpar()
        logger.info("Memória semântica limpa")
