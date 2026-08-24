"""
Registro de Capacidades — Projeto Orion.

Permite ao Orquestrador consultar dinamicamente quais provedores
podem atender cada tipo de tarefa, sem conhecer implementações concretas.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class DominioTarefa(Enum):
    """Domínios de tarefa que uma IA pode realizar."""

    CONVERSACAO = "conversacao"
    RACIOCINIO_LOGICO = "raciocinio"
    MATEMATICA = "matematica"
    PROGRAMACAO = "programacao"
    MEDICINA = "medicina"
    DIREITO = "direito"
    CIENCIAS = "ciencias"
    IMAGENS = "imagens"
    VIDEO = "video"
    AUDIO = "audio"
    TRADUCAO = "traducao"
    PESQUISA = "pesquisa"
    DADOS = "dados"
    QUANTUM = "quantum"
    IOT = "iot"
    SEGURANCA = "seguranca"


@dataclass(frozen=True, kw_only=True)
class PerfilCapacidade:
    """Perfil de capacidade de um modelo específico."""

    modelo: str
    provedor: str
    scores: Dict[DominioTarefa, float] = field(default_factory=dict)
    max_tokens_contexto: int = 4096
    suporta_streaming: bool = True

    def score_para(self, dominio: DominioTarefa) -> float:
        """Retorna o score para um domínio."""
        return self.scores.get(dominio, 0.0)

    def suporta(self, dominio: DominioTarefa) -> bool:
        """Verifica se suporta o domínio."""
        return self.score_para(dominio) > 0.0

    def eh_especialista(self, dominio: DominioTarefa) -> bool:
        """Verifica se é especialista no domínio."""
        return self.score_para(dominio) >= 0.8


class RegistroCapacidades:
    """Registro central de capacidades — Versão 1.0."""

    def __init__(self):
        self._perfis: Dict[str, PerfilCapacidade] = {}

    def registrar(self, perfil: PerfilCapacidade) -> None:
        """Registra ou atualiza o perfil de um modelo."""
        self._perfis[perfil.modelo] = perfil

    def remover(self, modelo: str) -> None:
        """Remove um modelo do registro."""
        self._perfis.pop(modelo, None)

    def obter_perfil(self, modelo: str) -> Optional[PerfilCapacidade]:
        """Retorna o perfil de um modelo específico."""
        return self._perfis.get(modelo)

    def buscar_por_dominio(
        self,
        dominio: DominioTarefa,
    ) -> List[PerfilCapacidade]:
        """Busca todos os modelos que suportam um domínio."""
        return [
            perfil
            for perfil in self._perfis.values()
            if perfil.suporta(dominio)
        ]

    def listar_todos(self) -> List[PerfilCapacidade]:
        """Lista todos os modelos registrados."""
        return list(self._perfis.values())

    def obter_provedor_para_modelo(
        self,
        modelo: str,
    ) -> Optional[str]:
        """Retorna o nome do provedor para um modelo."""
        perfil = self._perfis.get(modelo)
        return perfil.provedor if perfil else None
