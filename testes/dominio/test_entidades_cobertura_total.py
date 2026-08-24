"""
Testes unitários complementares para atingir 100% de cobertura no mestre_ia.dominio.entidades.
"""

import pytest
from datetime import datetime, timezone
from mestre_ia.dominio.entidades import (
    NivelEvidencia,
    ReferenciaCientifica,
    Evidencia,
    Paciente,
    Diagnostico,
)


class TestReferenciaCientificaEFormatacao:
    """Testes para a classe ReferenciaCientifica e formatação de citação."""

    def test_referencia_valida(self):
        ref = ReferenciaCientifica(
            titulo="Estudo sobre IA em Saúde",
            autores=["Silva, A.", "Santos, B."],
            ano=2023,
            doi="10.1000/182",
            url="https://example.com"
        )
        assert ref.titulo == "Estudo sobre IA em Saúde"
        assert ref.ano == 2023

    def test_referencia_ano_invalido_baixo(self):
        with pytest.raises(ValueError, match="Ano de publicação inválido"):
            ReferenciaCientifica(
                titulo="Manuscrito Antigo",
                autores=["Autor X"],
                ano=1499
            )

    def test_referencia_ano_invalido_futuro(self):
        ano_futuro = datetime.now(timezone.utc).year + 5
        with pytest.raises(ValueError, match="Ano de publicação inválido"):
            ReferenciaCientifica(
                titulo="Estudo do Futuro",
                autores=["Autor X"],
                ano=ano_futuro
            )

    def test_referencia_sem_autores(self):
        with pytest.raises(ValueError, match="pelo menos um autor"):
            ReferenciaCientifica(
                titulo="Sem Autor",
                autores=[],
                ano=2020
            )

    def test_formatar_citacao_apa(self):
        ref = ReferenciaCientifica(
            titulo="Algoritmos de Diagnóstico",
            autores=["Oliveira, C.", "Costa, D."],
            ano=2021
        )
        assert ref.formatar_citacao("apa") == "Oliveira, C. et al. (2021). Algoritmos de Diagnóstico."

    def test_formatar_citacao_vancouver(self):
        ref = ReferenciaCientifica(
            titulo="Algoritmos de Diagnóstico",
            autores=["Oliveira, C.", "Costa, D."],
            ano=2021
        )
        assert ref.formatar_citacao("vancouver") == "Oliveira, C., Costa, D.. Algoritmos de Diagnóstico. 2021."

    def test_formatar_citacao_estilo_invalido(self):
        ref = ReferenciaCientifica(
            titulo="Algoritmos de Diagnóstico",
            autores=["Oliveira, C."],
            ano=2021
        )
        with pytest.raises(ValueError, match="Estilo 'abnt' não suportado"):
            ref.formatar_citacao("abnt")


class TestEvidenciaEResumo:
    """Testes para a classe Evidencia e método resumo."""

    def test_evidencia_afirmacao_vazia(self):
        with pytest.raises(ValueError, match="A afirmação não pode estar vazia"):
            Evidencia(afirmacao="   ", nivel=NivelEvidencia.COORTE)

    def test_evidencia_nivel_alto_sem_referencia_gera_alerta(self):
        ev = Evidencia(
            afirmacao="Tratamento X reduz mortalidade",
            nivel=NivelEvidencia.META_ANALISE,
            referencias=[]
        )
        assert "[ALERTA: Nível alto sem referências listadas]" in ev.limitacoes

    def test_evidencia_resumo_fato_comprovado(self):
        ref = ReferenciaCientifica(titulo="Estudo A", autores=["A"], ano=2020)
        ev = Evidencia(
            afirmacao="Vacinas funcionam",
            nivel=NivelEvidencia.META_ANALISE,
            referencias=[ref],
            e_fato_comprovado=True
        )
        resumo = ev.resumo()
        assert "FATO COMPROVADO" in resumo
        assert "Afirmação: Vacinas funcionam" in resumo
        assert "1 referência(s)" in resumo

    def test_evidencia_resumo_nao_fato_comprovado(self):
        ev = Evidencia(
            afirmacao="Hipótese sob investigação",
            nivel=NivelEvidencia.SERIE_CASOS,
            referencias=[]
        )
        resumo = ev.resumo()
        assert "EVIDÊNCIA CIENTÍFICA" in resumo


class TestNivelEvidenciaEnum:
    """Testes para a enumeração NivelEvidencia."""

    def test_str_nivel_evidencia(self):
        nivel = NivelEvidencia.META_ANALISE
        assert str(nivel) == "Nível 1: Revisão Sistemática / Meta-análise de RCTs"


class TestPacienteEDiagnosticoValidacoes:
    """Validações adicionais para Paciente e Diagnostico."""

    def test_paciente_nome_vazio(self):
        with pytest.raises(ValueError, match="Nome do paciente é obrigatório"):
            Paciente(nome="   ", idade=30)

    def test_paciente_idade_invalida_negativa(self):
        with pytest.raises(ValueError, match="Idade inválida: -1"):
            Paciente(nome="João", idade=-1)

    def test_paciente_idade_invalida_alta(self):
        with pytest.raises(ValueError, match="Idade inválida: 151"):
            Paciente(nome="João", idade=151)

    def test_diagnostico_condicao_vazia(self):
        with pytest.raises(ValueError, match="Condição é obrigatória"):
            Diagnostico(condicao="  ", probabilidade=0.5)

    @pytest.mark.parametrize("prob_invalida", [-0.1, 1.1])
    def test_diagnostico_probabilidade_invalida(self, prob_invalida):
        with pytest.raises(ValueError, match="Probabilidade deve estar entre 0.0 e 1.0"):
            Diagnostico(condicao="Infecção", probabilidade=prob_invalida)
