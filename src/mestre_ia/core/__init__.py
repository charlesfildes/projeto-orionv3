"""
Módulo Core do Projeto Orion.

Exporta as abstrações principais, container de dependências,
configurações e sistema de plugins.
"""

from mestre_ia.core.configuracao import Configuracao
from mestre_ia.core.container import ContainerDependencia
from mestre_ia.core.excecoes import (
    ErroConfiguracao,
    ErroDominio,
    ErroInfraestrutura,
    MestreIAError,
)

# Aliases para compatibilidade de nomes legados
ErroBaseOrion = MestreIAError
ErroValidacao = ErroDominio
ErroIncializacao = ErroConfiguracao

from mestre_ia.core.logging_estruturado import obter_logger
from mestre_ia.core.plugins import EstadoPlugin, MetadadosPlugin, PluginBase

__all__ = [
    "Configuracao",
    "ContainerDependencia",
    "ErroBaseOrion",
    "ErroConfiguracao",
    "ErroDominio",
    "ErroIncializacao",
    "ErroInfraestrutura",
    "ErroValidacao",
    "MestreIAError",
    "obter_logger",
    "EstadoPlugin",
    "MetadadosPlugin",
    "PluginBase",
]
