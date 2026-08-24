#!/bin/bash
# Script para criar estrutura de testes do Projeto Orion

echo "Criando diretórios..."
mkdir -p testes/core testes/dominio testes/aplicacao testes/interfaces/cli testes/memoria

echo "Criando arquivos __init__.py..."
touch testes/__init__.py testes/core/__init__.py testes/dominio/__init__.py \
      testes/aplicacao/__init__.py testes/interfaces/__init__.py \
      testes/interfaces/cli/__init__.py testes/memoria/__init__.py

echo "Criando arquivos de teste..."

# Criar test_entidades.py
cat << 'EOF' > testes/dominio/test_entidades.py
import pytest
from mestre_ia.dominio.entidades import NivelEvidencia, ReferenciaCientifica, Evidencia, Paciente, Diagnostico

class TestNivelEvidencia:
    def test_comparacao_niveis(self):
        assert NivelEvidencia.META_ANALISE.value < NivelEvidencia.OPINIAO_ESPECIALISTA.value

class TestReferenciaCientifica:
    def test_criacao_valida(self):
        ref = ReferenciaCientifica(titulo="Estudo", autores=["Silva, J."], ano=2024)
        assert ref.titulo == "Estudo"

class TestPaciente:
    def test_criacao_valida(self):
        paciente = Paciente(nome="Maria", idade=45)
        assert paciente.nome == "Maria"
EOF

# Criar test_principal.py
cat << 'EOF' > testes/interfaces/cli/test_principal.py
import pytest
from typer.testing import CliRunner
from mestre_ia.interfaces.cli.principal import app

class TestCLI:
    def test_app_existe(self):
        assert app is not None
EOF

# Criar test_container.py
cat << 'EOF' > testes/core/test_container.py
import pytest
from mestre_ia.core.container import ContainerDependencia

class TestContainerDependencia:
    def test_registrar_e_obter(self):
        container = ContainerDependencia()
        class Interface: pass
        class Implementacao(Interface): pass
        container.registrar(Interface, Implementacao)
        assert isinstance(container.obter(Interface), Implementacao)
EOF

echo "Estrutura criada com sucesso!"
