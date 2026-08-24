"""
Adaptadores de Computação Quântica — Projeto Orion.
Suporta:
- Origin Quantum (QPanda) via SDK local
- IBM Quantum (Qiskit) — futuro
"""

from .qpanda_adapter import QPandaAdapter

__all__ = ["QPandaAdapter"]
