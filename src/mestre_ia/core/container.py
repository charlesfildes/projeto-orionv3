"""
Container de Injeção de Dependência — Projeto Orion.

Implementa um contêiner IoC (Inversion of Control) simples e explícito.
Resolve dependências automaticamente por tipo.

Princípios:
- EXPLÍCITO MELHOR QUE IMPLÍCITO: Registro manual, resolução automática
- SEM MÁGICA: Nada de scan de pacotes ou convenções obscuras
- TESTÁVEL: Fácil de substituir dependências para testes
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, Optional, Callable, TypeVar

T = TypeVar('T')


class ContainerDependencia:
    """
    Container de Inversão de Controle.

    Suporta escopos:
    - singleton: uma única instância durante toda a vida do container
    - transient: uma nova instância a cada resolução

    Uso:
        container = ContainerDependencia()
        container.registrar(Interface, Implementacao, escopo="singleton")
        instancia = container.obter(Interface)
    """

    def __init__(self):
        self._registros: Dict[type, Dict[str, Any]] = {}
        self._singletons: Dict[type, Any] = {}
        self._em_resolucao: set = set()

    def registrar(
        self,
        interface: type[T],
        implementacao: type[T],
        escopo: str = "singleton",
        fabrica: Optional[Callable[[], T]] = None,
    ) -> None:
        """
        Registra uma implementação para uma interface.

        Args:
            interface: Tipo abstrato (porta/protocolo)
            implementacao: Classe concreta que implementa a interface
            escopo: "singleton" (padrão) ou "transient"
            fabrica: Função opcional que cria a instância

        Raises:
            ValueError: Se o escopo for inválido
        """
        escopos_validos = {"singleton", "transient"}
        if escopo not in escopos_validos:
            raise ValueError(
                f"Escopo '{escopo}' inválido. Use: {sorted(escopos_validos)}"
            )

        self._registros[interface] = {
            "implementacao": implementacao,
            "escopo": escopo,
            "fabrica": fabrica,
        }

    def obter(self, interface: type[T]) -> T:
        """
        Obtém uma instância da interface solicitada.

        Resolve:
        1. Se singleton, retorna a instância cacheada
        2. Se tem fábrica registrada, usa a fábrica
        3. Caso contrário, cria nova instância (sem inspeção de __init__)

        Args:
            interface: Tipo abstrato desejado

        Returns:
            Instância concreta da interface

        Raises:
            KeyError: Se a interface não foi registrada
        """
        # 1. Verificar singleton cacheado
        if interface in self._singletons:
            return self._singletons[interface]

        # 2. Obter registro
        registro = self._registros.get(interface)
        if not registro:
            raise KeyError(
                f"Nenhuma implementação registrada para '{interface.__name__}'. "
                f"Use container.registrar({interface.__name__}, ...) antes de obter."
            )

        # 3. Detectar dependências circulares
        if interface in self._em_resolucao:
            raise RuntimeError(
                f"Dependência circular detectada ao resolver '{interface.__name__}'."
            )
        self._em_resolucao.add(interface)

        try:
            # 4. Criar instância
            instancia = self._criar_instancia(registro)

            # 5. Cache se singleton
            if registro["escopo"] == "singleton":
                self._singletons[interface] = instancia

            return instancia
        finally:
            self._em_resolucao.discard(interface)

    def _criar_instancia(self, registro: Dict[str, Any]) -> Any:
        """
        Cria uma instância sem inspeção de __init__.
        Usa fábrica se fornecida, caso contrário chama a classe sem argumentos.
        """
        # Caso 1: Fábrica explícita
        if registro["fabrica"]:
            return registro["fabrica"]()

        # Caso 2: Classe sem argumentos (comportamento simples e previsível)
        classe = registro["implementacao"]
        return classe()

    def limpar_cache(self) -> None:
        """Limpa o cache de singletons. Útil para testes."""
        self._singletons.clear()

    def registrar_singleton_direto(
        self,
        interface: type[T],
        instancia: T,
    ) -> None:
        """
        Registra uma instância já criada como singleton.

        Args:
            interface: Tipo da interface
            instancia: Instância concreta
        """
        self._singletons[interface] = instancia


container_global = ContainerDependencia()


def obter_container() -> ContainerDependencia:
    """Retorna a instância global do container de dependências."""
    return container_global
