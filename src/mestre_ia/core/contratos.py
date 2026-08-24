"""
Módulo de contratos (portas) da arquitetura hexagonal.

Define todas as interfaces formais (Protocols) que desacoplam
o núcleo da aplicação das implementações concretas.

Princípios:
- Interface Segregation Principle (SOLID)
- Dependency Inversion Principle (SOLID)
- Protocol classes (PEP 544) para verificação estrutural
- Versionamento de contratos (VERSAO_CONTRATO)
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Protocol,
)
from enum import Enum
from datetime import datetime, timezone
import uuid


# ============================================================================
# TIPOS FUNDAMENTAIS (usados por todos os contratos)
# ============================================================================

class TipoProvedorIA(Enum):
    """
    Identificador único para cada provedor de IA suportado.
    Novos provedores podem ser adicionados sem alterar código existente
    (Open/Closed Principle).
    """
    CHATGPT = "chatgpt"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    KIMI = "kimi"
    QWEN = "qwen"
    MISTRAL = "mistral"
    LOCAL = "local"
    PERSONALIZADO = "personalizado"


class TipoBackendQuantico(Enum):
    """Backends de computação quântica suportados."""
    IBM_QUANTUM = "ibm_quantum"
    ORIGIN_QUANTUM = "origin_quantum"
    SIMULADOR_LOCAL = "simulador"
    AWS_BRAKET = "aws_braket"
    IONQ = "ionq"


class PrioridadeTarefa(Enum):
    """Níveis de prioridade para fila de tarefas."""
    CRITICA = 0
    ALTA = 1
    MEDIA = 2
    BAIXA = 3
    BACKGROUND = 4


class EstadoTarefa(Enum):
    """Estados do ciclo de vida de uma tarefa."""
    CRIADA = "criada"
    ENFILEIRADA = "enfileirada"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"
    FALHA = "falha"
    CANCELADA = "cancelada"
    REJEITADA = "rejeitada"


@dataclass(frozen=True, kw_only=True)
class RequisicaoIA:
    """
    Objeto de valor imutável que representa uma requisição a uma IA.
    Todo adaptador deve aceitar este formato e convertê-lo para a API nativa.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    contexto_sistema: Optional[str] = None
    historico: List[Dict[str, str]] = field(default_factory=list)
    parametros: Dict[str, Any] = field(default_factory=dict)
    provedor_preferido: Optional[TipoProvedorIA] = None
    prioridade: PrioridadeTarefa = PrioridadeTarefa.MEDIA
    metadados: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.prompt.strip():
            raise ValueError("Prompt não pode estar vazio")


@dataclass(frozen=True, kw_only=True)
class RespostaIA:
    """
    Objeto de valor imutável que normaliza a resposta de qualquer provedor.
    """
    conteudo: str
    provedor: TipoProvedorIA
    modelo: str
    tokens_entrada: int = 0
    tokens_saida: int = 0
    tempo_resposta_ms: float = 0.0
    metadados: Dict[str, Any] = field(default_factory=dict)
    requisicao_id: Optional[str] = None

    def __post_init__(self):
        if self.tokens_entrada < 0:
            raise ValueError(
                f"tokens_entrada não pode ser negativo: {self.tokens_entrada}"
            )
        if self.tokens_saida < 0:
            raise ValueError(
                f"tokens_saida não pode ser negativo: {self.tokens_saida}"
            )
        if self.tempo_resposta_ms < 0:
            raise ValueError(
                f"tempo_resposta_ms não pode ser negativo: {self.tempo_resposta_ms}"
            )


@dataclass(frozen=True, kw_only=True)
class CircuitoQuantico:
    """Representação abstrata de um circuito quântico."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    num_qubits: int
    operacoes: List[Dict[str, Any]]
    medicao: List[int]

    def __post_init__(self):
        if self.num_qubits <= 0:
            raise ValueError(
                f"num_qubits deve ser maior que zero: {self.num_qubits}"
            )
        if not self.operacoes:
            raise ValueError("operacoes não pode estar vazia")
        if not self.medicao:
            raise ValueError("medicao não pode estar vazia")
        for indice in self.medicao:
            if indice < 0 or indice >= self.num_qubits:
                raise ValueError(
                    f"Índice de medição inválido: {indice}. "
                    f"Deve estar entre 0 e {self.num_qubits - 1}"
                )


@dataclass(frozen=True, kw_only=True)
class ResultadoQuantico:
    """Resultado normalizado de uma execução quântica."""
    contagens: Dict[str, int]
    provedor: TipoBackendQuantico
    tempo_execucao_ms: float
    metadados: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.tempo_execucao_ms < 0:
            raise ValueError(
                f"tempo_execucao_ms não pode ser negativo: {self.tempo_execucao_ms}"
            )
        for chave, valor in self.contagens.items():
            if valor < 0:
                raise ValueError(
                    f"Contagem negativa para '{chave}': {valor}"
                )


# ============================================================================
# PORTAS (INTERFACES)
# ============================================================================

class IAProviderPort(Protocol):
    """
    Porta para provedores de IA — v1.0
    """
    VERSAO_CONTRATO: str = "1.0"

    @property
    def provedor(self) -> TipoProvedorIA: ...

    @property
    def modelos_disponiveis(self) -> List[str]: ...

    async def enviar_prompt(
        self, requisicao: RequisicaoIA, timeout_ms: int = 30000
    ) -> RespostaIA: ...

    async def enviar_prompt_streaming(
        self, requisicao: RequisicaoIA, timeout_ms: int = 60000
    ) -> AsyncIterator[str]: ...


class QuantumBackendPort(Protocol):
    """Porta para backends quânticos — v1.0"""
    VERSAO_CONTRATO: str = "1.0"

    @property
    def backend(self) -> TipoBackendQuantico: ...

    @property
    def num_qubits_disponiveis(self) -> int: ...

    async def executar_circuito(
        self, circuito: CircuitoQuantico, shots: int = 1024
    ) -> ResultadoQuantico: ...

    async def obter_estado_vetor(
        self, circuito: CircuitoQuantico
    ) -> List[complex]: ...


class RepositorioPort(Protocol):
    """Porta genérica para persistência — v1.0"""
    VERSAO_CONTRATO: str = "1.0"

    async def salvar(self, entidade: Any, tipo: str) -> str: ...
    async def buscar_por_id(self, id: str, tipo: str) -> Optional[Any]: ...
    async def listar(
        self, tipo: str, filtros: Optional[Dict[str, Any]] = None
    ) -> List[Any]: ...
    async def remover(self, id: str, tipo: str) -> bool: ...


class AutenticacaoPort(Protocol):
    """Porta para autenticação e autorização — v1.0"""
    VERSAO_CONTRATO: str = "1.0"

    async def autenticar_credenciais(
        self, usuario: str, senha: str
    ) -> Optional[Dict[str, Any]]: ...
    async def validar_token(self, token: str) -> Optional[Dict[str, Any]]: ...
    async def verificar_permissao(
        self, token: str, recurso: str, acao: str
    ) -> bool: ...
    async def revogar_token(self, token: str) -> bool: ...


# ============================================================================
# EVENTOS E BARRAMENTO
# ============================================================================

class EventoDominio(ABC):
    """Classe base para todos os eventos de domínio."""
    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self.timestamp: datetime = datetime.now(timezone.utc)
        self.nome: str = self.__class__.__name__


class ManipuladorEventosPort(Protocol):
    """Porta para barramento de eventos (Event Bus)."""
    async def publicar(self, evento: EventoDominio) -> None: ...
    async def assinar(
        self,
        tipo_evento: type,
        callback: Callable[[EventoDominio], Coroutine[Any, Any, None]],
    ) -> None: ...
