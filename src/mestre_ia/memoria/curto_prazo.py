"""
Memória de Curto Prazo para o Projeto Orion.

Gerencia o histórico da conversa recente mantendo contexto em janela deslizante.
"""

from typing import List, Dict, Any, Optional


class MemoriaCurtoPrazo:
    """
    Gerenciador de memória de curto prazo baseada em mensagens recentes.
    """

    def __init__(self, limite_mensagens: int = 10):
        self._limite = limite_mensagens
        self._historico: List[Dict[str, str]] = []

    def adicionar_mensagem(self, papel: str, conteudo: str) -> None:
        """Adiciona uma mensagem (user, assistant, system) ao histórico."""
        self._historico.append({"role": papel, "content": conteudo})
        if len(self._historico) > self._limite:
            self._historico.pop(0)

    def obter_historico(self) -> List[Dict[str, str]]:
        """Retorna uma cópia das mensagens armazenadas."""
        return list(self._historico)

    def limpar(self) -> None:
        """Limpa o histórico armazenado."""
        self._historico.clear()
