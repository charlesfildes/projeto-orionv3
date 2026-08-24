"""
Sistema de Plugins — Projeto Orion.

Framework de extensão que permite adicionar novas funcionalidades
sem modificar o núcleo da aplicação.

Princípios:
1. Plugins são auto-contidos e independentes
2. Descoberta dinâmica via entry points ou diretórios
3. Cada plugin declara suas dependências e versão
4. Plugins não podem modificar o núcleo
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EstadoPlugin(Enum):
    """Estados possíveis de um plugin."""
    NAO_CARREGADO = "nao_carregado"
    CARREGADO = "carregado"
    INICIALIZADO = "inicializado"
    ATIVO = "ativo"
    ERRO = "erro"
    DESATIVADO = "desativado"


@dataclass(kw_only=True)
class MetadadosPlugin:
    """Metadados de um plugin."""
    nome: str
    versao: str
    descricao: str = ""
    autor: str = ""
    dependencias: List[str] = field(default_factory=list)
    versao_minima_core: str = "1.0.0"
    compativel_ate_core: str = "1.9.9"


class PluginBase(ABC):
    """Classe base para todos os plugins do Projeto Orion."""
    
    def __init__(self):
        self._estado = EstadoPlugin.NAO_CARREGADO
        self._erro: Optional[Exception] = None
    
    @property
    @abstractmethod
    def metadados(self) -> MetadadosPlugin:
        """Metadados descritivos do plugin."""
        ...
    
    @abstractmethod
    def inicializar(self, container: Any) -> None:
        """Inicializa o plugin."""
        ...
    
    @abstractmethod
    def finalizar(self, container: Any) -> None:
        """Finaliza o plugin."""
        ...
    
    @property
    def estado(self) -> EstadoPlugin:
        return self._estado
    
    @property
    def erro(self) -> Optional[Exception]:
        return self._erro
    
    def __str__(self) -> str:
        return f"{self.metadados.nome} v{self.metadados.versao} [{self._estado.value}]"


class GerenciadorPlugins:
    """Gerenciador de plugins — Versão 2.0 (RESERVADO)"""
    
    def __init__(self, container: Any):
        self._container = container
        self._plugins: Dict[str, PluginBase] = {}
        raise NotImplementedError("GerenciadorPlugins será implementado na Versão 2.0.")
