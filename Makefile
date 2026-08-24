GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
BLUE   := \033[0;34m
NC     := \033[0m

PYTHON := $(shell command -v python3.12 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3 2>/dev/null || echo python3)
PYTEST := $(HOME)/Orion/venv/bin/pytest
RUFF   := $(HOME)/Orion/venv/bin/ruff
BLACK  := $(HOME)/Orion/venv/bin/black

.DEFAULT_GOAL := help

help:
	@echo "$(GREEN)Projeto Orion — Comandos$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install:
	@echo "$(GREEN)Use: source ~/Orion/venv/bin/activate && pip install -e .$(NC)"

test:
	@cd ~/Orion/projeto-orion && $(PYTEST) testes/ -v

test-cov:
	@cd ~/Orion/projeto-orion && $(PYTEST) testes/ -v --cov=mestre_ia --cov-report=term-missing

lint:
	@$(RUFF) check src/ testes/

format:
	@$(RUFF) format src/ testes/
	@$(BLACK) src/ testes/

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)Limpeza concluída!$(NC)"

info:
	@echo "Python: $$($(PYTHON) --version 2>/dev/null || echo 'NÃO ENCONTRADO')"
	@echo "Virtualenv: ~/Orion/venv"

.PHONY: help install test test-cov lint format clean info
