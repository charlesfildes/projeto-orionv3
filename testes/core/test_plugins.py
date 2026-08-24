"""
Testes unitários para o módulo de Plugins (core/plugins.py).
"""

import pytest
from mestre_ia.core.plugins import (
    EstadoPlugin,
    GerenciadorPlugins,
    MetadadosPlugin,
    PluginBase,
)


class PluginExemplo(PluginBase):
    """Implementação concreta de teste para PluginBase."""

    @property
    def metadados(self) -> MetadadosPlugin:
        return MetadadosPlugin(
            nome="plugin-teste",
            versao="1.0.0",
            descricao="Plugin de teste unitário",
            autor="Dev Team",
            dependencias=["pytest"],
        )

    def inicializar(self, container):
        self._estado = EstadoPlugin.ATIVO

    def finalizar(self, container):
        self._estado = EstadoPlugin.DESATIVADO


class TestEstadoPlugin:
    """Testes para o Enum EstadoPlugin."""

    def test_valores_do_enum(self):
        assert EstadoPlugin.NAO_CARREGADO.value == "nao_carregado"
        assert EstadoPlugin.CARREGADO.value == "carregado"
        assert EstadoPlugin.INICIALIZADO.value == "inicializado"
        assert EstadoPlugin.ATIVO.value == "ativo"
        assert EstadoPlugin.ERRO.value == "erro"
        assert EstadoPlugin.DESATIVADO.value == "desativado"


class TestMetadadosPlugin:
    """Testes para a dataclass MetadadosPlugin."""

    def test_valores_padrao(self):
        meta = MetadadosPlugin(nome="demo", versao="0.1.0")
        assert meta.nome == "demo"
        assert meta.versao == "0.1.0"
        assert meta.descricao == ""
        assert meta.autor == ""
        assert meta.dependencias == []
        assert meta.versao_minima_core == "1.0.0"
        assert meta.compativel_ate_core == "1.9.9"

    def test_valores_customizados(self):
        meta = MetadadosPlugin(
            nome="meu-plugin",
            versao="2.0.0",
            descricao="Descrição personalizada",
            autor="Carlos",
            dependencias=["requests", "pydantic"],
            versao_minima_core="1.2.0",
            compativel_ate_core="2.0.0",
        )
        assert meta.nome == "meu-plugin"
        assert meta.autor == "Carlos"
        assert len(meta.dependencias) == 2


class TestPluginBase:
    """Testes para a classe abstrata PluginBase e suas instâncias."""

    def test_instanciacao_e_estado_inicial(self):
        plugin = PluginExemplo()
        assert plugin.estado == EstadoPlugin.NAO_CARREGADO
        assert plugin.erro is None
        assert str(plugin) == "plugin-teste v1.0.0 [nao_carregado]"

    def test_ciclo_de_vida_inicializar_e_finalizar(self):
        plugin = PluginExemplo()
        container_falso = object()

        plugin.inicializar(container_falso)
        assert plugin.estado == EstadoPlugin.ATIVO
        assert str(plugin) == "plugin-teste v1.0.0 [ativo]"

        plugin.finalizar(container_falso)
        assert plugin.estado == EstadoPlugin.DESATIVADO
        assert str(plugin) == "plugin-teste v1.0.0 [desativado]"

    def test_nao_pode_instanciar_classe_abstrata_sem_metodos(self):
        with pytest.raises(TypeError):
            PluginBase()


class TestGerenciadorPlugins:
    """Testes para a classe reservada GerenciadorPlugins."""

    def test_gerenciador_plugins_lanca_not_implemented_error(self):
        container_falso = object()
        with pytest.raises(NotImplementedError) as exc_info:
            GerenciadorPlugins(container_falso)

        assert "GerenciadorPlugins será implementado na Versão 2.0" in str(exc_info.value)
