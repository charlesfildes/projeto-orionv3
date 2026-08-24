"""
Testes unitários completos do Container de Injeção de Dependências.
"""

import pytest
from mestre_ia.core.container import ContainerDependencia


class TestContainerDependencia:
    """Suíte de testes para validação completa do ContainerDependencia."""

    @pytest.fixture(autouse=True)
    def resetar_container(self):
        """Isola os testes criando um novo container para cada teste."""
        container = ContainerDependencia()
        yield container

    def test_registrar_e_obter_singleton(self):
        """Deve registrar e obter uma implementação singleton."""
        container = ContainerDependencia()

        class Interface:
            pass

        class Implementacao(Interface):
            pass

        container.registrar(Interface, Implementacao, escopo="singleton")
        instancia = container.obter(Interface)

        assert isinstance(instancia, Implementacao)

    def test_singleton_retorna_mesma_instancia(self):
        """Singleton deve retornar a mesma instância."""
        container = ContainerDependencia()

        class Interface:
            pass

        class Implementacao(Interface):
            pass

        container.registrar(Interface, Implementacao, escopo="singleton")
        inst1 = container.obter(Interface)
        inst2 = container.obter(Interface)

        assert inst1 is inst2

    def test_transient_retorna_instancias_diferentes(self):
        """Transient deve retornar instâncias diferentes."""
        container = ContainerDependencia()

        class Interface:
            pass

        class Implementacao(Interface):
            pass

        container.registrar(Interface, Implementacao, escopo="transient")
        inst1 = container.obter(Interface)
        inst2 = container.obter(Interface)

        assert inst1 is not inst2

    def test_obter_dependencia_nao_registrada_lanca_excecao(self):
        """Deve lançar erro para interface não registrada."""
        container = ContainerDependencia()

        class Interface:
            pass

        with pytest.raises(KeyError):
            container.obter(Interface)

    def test_escopo_invalido(self):
        """Deve rejeitar escopo inválido."""
        container = ContainerDependencia()

        class Interface:
            pass

        class Implementacao(Interface):
            pass

        with pytest.raises(ValueError):
            container.registrar(Interface, Implementacao, escopo="invalido")

    def test_registrar_singleton_direto(self):
        """Deve registrar instância diretamente."""
        container = ContainerDependencia()

        class Interface:
            pass

        instancia = object()
        container.registrar_singleton_direto(Interface, instancia)

        assert container.obter(Interface) is instancia

    def test_limpar_cache(self):
        """Deve limpar cache de singletons."""
        container = ContainerDependencia()

        class Interface:
            pass

        class Implementacao(Interface):
            pass

        container.registrar(Interface, Implementacao)
        inst1 = container.obter(Interface)
        container.limpar_cache()
        inst2 = container.obter(Interface)

        assert inst1 is not inst2
