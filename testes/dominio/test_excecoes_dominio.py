import pytest
from mestre_ia.dominio.excecoes_dominio import (
    BaseConhecimentoIndisponivelError,
    DiagnosticoInconsistenteError,
    EvidenciaInvalidaError,
    PacienteSemSintomasError,
    ReferenciaInvalidaError,
)


class TestExcecoesDominio:
    def test_base_conhecimento_indisponivel_error(self):
        erro_padrao = BaseConhecimentoIndisponivelError()
        assert str(erro_padrao) != ""

        erro_custom = BaseConhecimentoIndisponivelError("Falha na base de dados")
        assert "Falha na base de dados" in str(erro_custom)

    def test_diagnostico_inconsistente_error(self):
        erro = DiagnosticoInconsistenteError(
            condicao="Gripe",
            probabilidade=0.85,
            motivo="Falta de sintomas clássicos"
        )
        assert issubclass(DiagnosticoInconsistenteError, Exception)
        assert isinstance(erro, Exception)

    def test_evidencia_invalida_error(self):
        erro = EvidenciaInvalidaError(motivo="Evidência sem suporte estatístico")
        assert issubclass(EvidenciaInvalidaError, Exception)
        assert isinstance(erro, Exception)

    def test_paciente_sem_sintomas_error(self):
        erro = PacienteSemSintomasError(paciente_id="PAC-1234")
        assert issubclass(PacienteSemSintomasError, Exception)
        assert isinstance(erro, Exception)

    def test_referencia_invalida_error(self):
        erro = ReferenciaInvalidaError(campo="doi")
        assert issubclass(ReferenciaInvalidaError, Exception)
        assert isinstance(erro, Exception)
