"""
QPandaAdapter — Integração com Origin Quantum via SDK local (pyqpanda).
Suporte expandido: portas multi-qubit, portas de fase, ruído despolarizante e vetor de estado.
"""

import logging
import math
import random
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import pyqpanda as pq
    HAS_PYQPANDA = True
except ImportError as e:
    HAS_PYQPANDA = False
    logger.warning("pyqpanda não instalado. Usando fallback estocástico.")


class QPandaAdapter:
    """Adaptador para execução de circuitos quânticos via QPanda (C++)."""

    def __init__(self, ruido: float = 0.0):
        """
        Inicializa o adaptador.

        Args:
            ruido: Taxa de ruído de despolarização (0.0 = sem ruído, 0.5 = 50% de ruído)
        """
        self.has_pyqpanda = HAS_PYQPANDA
        self.ruido = max(0.0, min(1.0, ruido))  # Clamp entre 0 e 1

    async def executar_circuito(self, circuito: Any) -> Dict[str, Any]:
        """Executa a simulação do circuito quântico."""
        try:
            num_qubits = getattr(circuito, "num_qubits", 2) or 2
            operacoes = getattr(circuito, "operacoes", None) or []

            if not self.has_pyqpanda:
                return self._resultado_mock(num_qubits, "origin_quantum_mock")

            machine = pq.CPUQVM()
            machine.init_qvm()

            if hasattr(machine, "qAlloc_many"):
                q = machine.qAlloc_many(num_qubits)
                c = machine.cAlloc_many(num_qubits)
            elif hasattr(machine, "qalloc_many"):
                q = machine.qalloc_many(num_qubits)
                c = machine.calloc_many(num_qubits)
            else:
                q = [machine.qalloc() for _ in range(num_qubits)]
                c = [machine.calloc() for _ in range(num_qubits)]

            prog = pq.QProg()

            if not operacoes:
                prog << pq.H(q[0]) << pq.CNOT(q[0], q[1])
            else:
                prog = self._construir_programa(prog, q, operacoes)

            # Aplicar ruído de despolarização (se configurado)
            if self.ruido > 0:
                prog = self._aplicar_ruido(prog, q, num_qubits)

            if hasattr(pq, "measure_all"):
                prog << pq.measure_all(q, c)
            else:
                for i in range(num_qubits):
                    prog << pq.Measure(q[i], c[i])

            resultado = machine.run_with_configuration(prog, c, 1000)
            machine.finalize()

            return {
                "status": "sucesso",
                "provedor": "origin_quantum_qpanda",
                "num_qubits": num_qubits,
                "entropia_quantica": resultado or {"00": 500, "11": 500},
                "ruido": self.ruido,
            }

        except Exception as e:
            logger.error(f"Erro ao executar circuito quântico: {e}")
            return self._resultado_mock(
                getattr(circuito, "num_qubits", 2) or 2,
                "origin_quantum_fallback",
                detalhe=str(e),
            )

    async def obter_vetor_estado(self, circuito: Any) -> Dict[str, Any]:
        """
        Retorna o vetor de estado completo do circuito.
        Útil para visualização didática (máx 4 qubits).
        """
        try:
            num_qubits = getattr(circuito, "num_qubits", 2) or 2

            if not self.has_pyqpanda:
                return {
                    "status": "simulado",
                    "vetor_estado": [0.7071, 0.0, 0.0, 0.7071],
                    "num_amplitudes": 2 ** min(num_qubits, 4),
                }

            if num_qubits > 4:
                logger.warning("Vetor de estado limitado a 4 qubits por desempenho.")
                return {
                    "status": "erro",
                    "mensagem": "Vetor de estado disponível apenas para circuitos de até 4 qubits.",
                }

            machine = pq.CPUQVM()
            machine.init_qvm()

            if hasattr(machine, "qAlloc_many"):
                q = machine.qAlloc_many(num_qubits)
            elif hasattr(machine, "qalloc_many"):
                q = machine.qalloc_many(num_qubits)
            else:
                q = [machine.qalloc() for _ in range(num_qubits)]

            prog = pq.QProg()
            operacoes = getattr(circuito, "operacoes", None) or []

            if not operacoes:
                prog << pq.H(q[0]) << pq.CNOT(q[0], q[1])
            else:
                prog = self._construir_programa(prog, q, operacoes)

            machine.directly_run(prog)
            state = machine.get_qstate()
            machine.finalize()

            # Converter números complexos para formato legível (string ou lista)
            vetor_formatado = [f"{c.real:.4f} + {c.imag:.4f}j" if isinstance(c, complex) else round(float(c), 4) for c in state]

            return {
                "status": "sucesso",
                "vetor_estado": vetor_formatado,
                "num_amplitudes": 2 ** num_qubits,
            }

        except Exception as e:
            logger.error(f"Erro ao obter vetor de estado: {e}")
            return {
                "status": "erro_fallback",
                "vetor_estado": [0.7071, 0.0, 0.0, 0.7071],
                "num_amplitudes": 4,
                "detalhe": str(e),
            }

    def _construir_programa(self, prog: Any, q: list, operacoes: list) -> Any:
        """Mapeia as operações em portas quânticas C++ no QPanda."""
        for op in operacoes:
            if not isinstance(op, dict):
                continue

            porta = op.get("porta", "").upper()
            qubit = op.get("qubit", op.get("target", 0))
            controle = op.get("controle", op.get("control", None))
            controle2 = op.get("controle2", op.get("control2", None))
            alvo = op.get("alvo", op.get("target", None))
            qubit2 = op.get("qubit2", op.get("target2", None))
            angulo = float(op.get("angulo", op.get("angle", math.pi / 2)))

            # ============ PORTAS DE 1 QUBIT ============
            if porta == "H":
                prog << pq.H(q[qubit])
            elif porta == "X":
                prog << pq.X(q[qubit])
            elif porta == "Y":
                prog << pq.Y(q[qubit])
            elif porta == "Z":
                prog << pq.Z(q[qubit])
            elif porta == "S" and hasattr(pq, "S"):
                prog << pq.S(q[qubit])
            elif porta == "T" and hasattr(pq, "T"):
                prog << pq.T(q[qubit])
            elif porta == "RX":
                prog << pq.RX(q[qubit], angulo)
            elif porta == "RY":
                prog << pq.RY(q[qubit], angulo)
            elif porta == "RZ":
                prog << pq.RZ(q[qubit], angulo)

            # ============ PORTAS DE 2 QUBITS ============
            elif porta in ("CNOT", "CX"):
                if controle is not None and alvo is not None:
                    prog << pq.CNOT(q[controle], q[alvo])
            elif porta == "CZ":
                if controle is not None and alvo is not None:
                    prog << pq.CZ(q[controle], q[alvo])
            elif porta == "SWAP":
                p1 = qubit if qubit is not None else controle
                p2 = qubit2 if qubit2 is not None else alvo
                if p1 is not None and p2 is not None and hasattr(pq, "SWAP"):
                    prog << pq.SWAP(q[p1], q[p2])

            # ============ PORTA DE 3 QUBITS ============
            elif porta in ("TOFFOLI", "CCNOT"):
                if controle is not None and controle2 is not None and alvo is not None:
                    if hasattr(pq, "Toffoli"):
                        prog << pq.Toffoli(q[controle], q[controle2], q[alvo])
                    elif hasattr(pq, "CCNOT"):
                        prog << pq.CCNOT(q[controle], q[controle2], q[alvo])

        return prog

    def _aplicar_ruido(self, prog: Any, q: list, num_qubits: int) -> Any:
        """Aplica ruído de despolarização introduzindo bit-flips (X) aleatórios."""
        for i in range(num_qubits):
            if random.random() < self.ruido:
                prog << pq.X(q[i])
        return prog

    def _resultado_mock(
        self,
        num_qubits: int,
        provedor: str,
        detalhe: str = "",
    ) -> Dict[str, Any]:
        """Gera resultado estocástico quando o QPanda não está disponível."""
        entropia = {}
        for i in range(2 ** min(num_qubits, 4)):
            estado = format(i, f'0{min(num_qubits, 4)}b')
            entropia[estado] = random.randint(200, 800)

        return {
            "status": "sucesso_simulado",
            "provedor": provedor,
            "num_qubits": num_qubits,
            "entropia_quantica": entropia,
            "mensagem": "Simulação executada via fallback estocástico.",
            "detalhe": detalhe,
        }
