"""
Serviços de domínio do Projeto Orion.

Contém a lógica de negócio que não pertence naturalmente
a uma única entidade ou value object.
"""

from typing import List, Tuple

from .entidades import Paciente, Diagnostico, Evidencia, NivelEvidencia


class MotorDiagnosticoDiferencial:
    """
    Serviço de domínio para gerar diagnósticos diferenciais.

    Este serviço implementa lógica de negócio pura, sem dependências
    externas. Pode ser testado sem banco de dados, APIs ou frameworks.

    Responsabilidades:
    - Gerar lista de possíveis diagnósticos baseados em sintomas
    - Classificar por probabilidade
    - Associar evidências científicas a cada diagnóstico
    """

    def __init__(self, base_conhecimento: 'BaseConhecimentoMedica'):
        """
        Injeção de dependência: o motor recebe sua fonte de conhecimento,
        não a cria. Isso permite trocar a base sem modificar o motor.

        Args:
            base_conhecimento: Fonte de correlações sintoma-doença
        """
        self.base = base_conhecimento

    def gerar_diagnosticos(self, paciente: Paciente) -> List[Diagnostico]:
        """
        Gera diagnósticos diferenciais baseados nos sintomas do paciente.

        Algoritmo simplificado:
        1. Para cada sintoma, busca condições associadas
        2. Calcula score por condição
        3. Ordena por probabilidade decrescente
        4. Associa evidências da base de conhecimento

        Args:
            paciente: Paciente com sintomas relatados

        Returns:
            Lista de diagnósticos ordenada por probabilidade

        Raises:
            ValueError: Se paciente não tem sintomas
        """
        if not paciente.sintomas:
            raise ValueError(
                "Não é possível gerar diagnóstico: paciente não possui sintomas registrados."
            )

        scores: dict = {}
        evidencias_por_condicao: dict = {}

        # Fase 1: Coleta de evidências
        for sintoma in paciente.sintomas:
            condicoes_associadas = self.base.buscar_condicoes_por_sintoma(sintoma)

            for condicao, relevancia in condicoes_associadas:
                scores[condicao] = scores.get(condicao, 0.0) + relevancia

                if condicao not in evidencias_por_condicao:
                    evidencias_por_condicao[condicao] = []
                evidencias_por_condicao[condicao].append(sintoma)

        # Fase 2: Normalização e geração de diagnósticos
        total_sintomas = len(paciente.sintomas)
        diagnosticos = []

        for condicao, score in scores.items():
            probabilidade = min(score / total_sintomas, 1.0)

            evidencias = self.base.buscar_evidencias(condicao)

            diagnostico = Diagnostico(
                condicao=condicao,
                probabilidade=probabilidade,
                evidencias=evidencias,
                e_hipotese=True,
                notas=(
                    f"Baseado em {len(evidencias_por_condicao.get(condicao, []))} "
                    f"de {total_sintomas} sintomas relatados."
                )
            )
            diagnosticos.append(diagnostico)

        # Ordena do mais provável para o menos provável
        diagnosticos.sort(key=lambda d: d.probabilidade, reverse=True)

        return diagnosticos


class BaseConhecimentoMedica:
    """
    Interface abstrata para a base de conhecimento médico.

    Define o contrato que qualquer implementação concreta deve seguir.
    Isso é INVERSÃO DE DEPENDÊNCIA: o domínio define a interface,
    a infraestrutura a implementa.
    """

    def buscar_condicoes_por_sintoma(self, sintoma: str) -> List[Tuple[str, float]]:
        """
        Busca condições associadas a um sintoma.

        Args:
            sintoma: Descrição do sintoma

        Returns:
            Lista de tuplas (condição, relevância), onde relevância é 0.0-1.0
        """
        raise NotImplementedError("Subclasses devem implementar")

    def buscar_evidencias(self, condicao: str) -> List[Evidencia]:
        """
        Busca evidências científicas para uma condição.

        Args:
            condicao: Nome da condição médica

        Returns:
            Lista de evidências com níveis e referências
        """
        raise NotImplementedError("Subclasses devem implementar")

    def validar_contraindicacao(self, condicao: str, medicamento: str) -> bool:
        """
        Verifica se há contraindicação entre condição e medicamento.

        Args:
            condicao: Condição médica do paciente
            medicamento: Medicamento prescrito

        Returns:
            True se houver contraindicação, False caso contrário
        """
        raise NotImplementedError("Subclasses devem implementar")
