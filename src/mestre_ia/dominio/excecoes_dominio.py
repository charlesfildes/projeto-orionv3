""""
Exceções especáficas do domínio — Projeto Orion.

Estende a hierarquia de exceções do core para erros
relacionados a regras de negócio médicas.
"""

from mestre_ia.core.excecoes import (
    ErroDominio,
    ErroInfraestrutura,
)

class PacienteSemSintomasError(ErroDominio):
    """Tentativa de diagnóstico sem sintomas."""
    def __init__(self, paciente_id: str):
        super().__init__(
            mensagem=(
                "Não é possível gerar diagnóstico: "
                "paciente não possui sintomas registrados."
            ),
            codigo="PACIENTE_SEM_SINTOMAS",
            contexto={"paciente_id": paciente_id},
        )


class EvidenciaInvalidaError(ErroDominio):
    """Evidência não atende aos critérios de validação."""
    def __init__(self, motivo: str, afirmacao: str = ""):
        super().__init__(
            mensagem=f"Evidência inválida: {motivo}",
            codigo="EVIDENCIA_INVALIDA",
            contexto={"afirmacao": afirmacao[:100]},
        )


class DiagnosticoInconsistenteError(ErroDominio):
    """Diagnóstico viola regras de consistência médica."""
    def __init__(self, condicao: str, probabilidade: float, motivo: str):
        super().__init__(
            mensagem=f"Diagnóstico inconsistente para '{condicao}': {motivo}",
            codigo="DIAGNOSTICO_INCONSISTENTE",
            contexto={
                "condicao": condicao,
                "probabilidade": probabilidade,
                "motivo": motivo,
            },
        )


class ReferenciaInvalidaError(ErroDominio):
    """Referência científica não atende aos padrões."""
    def __init__(self, campo: str, valor: str = "", motivo: str = ""):
        super().__init__(
            mensagem=f"Referência inválida no campo '{campo}': {motivo}",
            codigo="REFERENCIA_INVALIDA",
            contexto={"campo": campo, "valor": valor},
        )


class BaseConhecimentoIndisponivelError(ErroInfraestrutura):
    """Base de conhecimento médico não está disponöel."""
    def __init__(self, detalhe: str = ""):
        super().__init__(
            mensagem=f"Base de conhecimento indisponível: {detalhe}",
            codigo="BASE_CONHECIMENTO_INDISPONIVEL",
            contexto={"detalhe": detalhe},
        )
