"""
Entidades do domínio — Projeto Orion.

Define os objetos centrais do negócio, independentes de infraestrutura.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class NivelEvidencia(Enum):
    """
    Enumeração para níveis de evidência científica.
    Baseado na hierarquia da Oxford Centre for Evidence-Based Medicine.
    """

    META_ANALISE = (1, "Revisão Sistemática / Meta-análise de RCTs")
    ENSAIO_RANDOMIZADO = (2, "Ensaio Clínico Randomizado Controlado")
    COORTE = (3, "Estudo de Coorte")
    SERIE_CASOS = (4, "Série de Casos / Caso-Controle")
    OPINIAO_ESPECIALISTA = (5, "Opinião de Especialista / Relato de Caso")

    def __new__(cls, valor: int, descricao: str):
        obj = object.__new__(cls)
        obj._value_ = valor
        obj.descricao = descricao
        return obj

    def __str__(self) -> str:
        return f"Nível {self.value}: {self.descricao}"


@dataclass(frozen=True, kw_only=True)
class ReferenciaCientifica:
    """Representa uma referência bibliográfica que fundamenta uma evidência."""

    titulo: str
    autores: List[str]
    ano: int
    doi: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        ano_atual = datetime.now(timezone.utc).year

        if not (1500 <= self.ano <= ano_atual + 1):
            raise ValueError(
                f"Ano de publicação inválido: {self.ano}. "
                f"Deve estar entre 1500 e {ano_atual + 1}."
            )

        if not self.autores:
            raise ValueError("É necessário pelo menos um autor.")

    def formatar_citacao(self, estilo: str = "apa") -> str:
        if estilo == "apa":
            return f"{self.autores[0]} et al. ({self.ano}). {self.titulo}."

        elif estilo == "vancouver":
            return f"{', '.join(self.autores)}. {self.titulo}. {self.ano}."

        else:
            raise ValueError(
                f"Estilo '{estilo}' não suportado. Use 'apa' ou 'vancouver'."
            )


@dataclass(frozen=True, kw_only=True)
class Evidencia:
    """Representa uma evidência científica com seu nível, afirmação e referências."""

    afirmacao: str
    nivel: NivelEvidencia
    referencias: List[ReferenciaCientifica] = field(default_factory=list)
    limitacoes: Optional[str] = None
    e_fato_comprovado: bool = False

    def __post_init__(self):
        if not self.afirmacao.strip():
            raise ValueError("A afirmação não pode estar vazia.")

        if self.nivel.value <= 2 and not self.referencias:
            object.__setattr__(
                self,
                "limitacoes",
                (self.limitacoes or "")
                + " [ALERTA: Nível alto sem referências listadas]",
            )

    def resumo(self) -> str:
        tipo = (
            "FATO COMPROVADO"
            if self.e_fato_comprovado
            else "EVIDÊNCIA CIENTÍFICA"
        )

        return (
            f"{tipo}\n"
            f"Afirmação: {self.afirmacao}\n"
            f"Nível: {self.nivel}\n"
            f"Referências: {len(self.referencias)} referência(s)"
        )


@dataclass(kw_only=True)
class Paciente:
    """Representa um paciente no sistema."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    idade: int
    sintomas: List[str] = field(default_factory=list)
    diagnosticos: List[Diagnostico] = field(default_factory=list)
    dados_vitais: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.nome.strip():
            raise ValueError("Nome do paciente é obrigatório.")

        if self.idade < 0 or self.idade > 150:
            raise ValueError(f"Idade inválida: {self.idade}")

    def adicionar_sintoma(self, sintoma: str) -> None:
        if sintoma.strip() and sintoma not in self.sintomas:
            self.sintomas.append(sintoma.strip())

    def adicionar_diagnostico(self, diagnostico: Diagnostico) -> None:
        self.diagnosticos.append(diagnostico)


@dataclass(kw_only=True)
class Diagnostico:
    """Representa um diagnóstico médico com suas evidências de suporte."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    condicao: str
    probabilidade: float
    evidencias: List[Evidencia] = field(default_factory=list)
    data: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    e_hipotese: bool = True
    notas: Optional[str] = None

    def __post_init__(self):
        if not self.condicao.strip():
            raise ValueError("Condição é obrigatória.")

        if not 0.0 <= self.probabilidade <= 1.0:
            raise ValueError(
                f"Probabilidade deve estar entre 0.0 e 1.0. "
                f"Recebido: {self.probabilidade}"
            )

    @property
    def probabilidade_percentual(self) -> float:
        return self.probabilidade * 100

    @property
    def classificacao_confianca(self) -> str:
        if self.probabilidade >= 0.9:
            return "ALTA CONFIANÇA"

        elif self.probabilidade >= 0.7:
            return "CONFIANÇA MODERADA"

        elif self.probabilidade >= 0.5:
            return "BAIXA CONFIANÇA"

        else:
            return "ESPECULATIVO - MAIS EXAMES RECOMENDADOS"
