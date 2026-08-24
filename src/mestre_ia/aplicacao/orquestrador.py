from typing import Dict, Optional

from mestre_ia.core.contratos import (
    IAProviderPort,
    RequisicaoIA,
    RespostaIA,
)
from mestre_ia.core.capacidades import (
    DominioTarefa,
    RegistroCapacidades,
)
from mestre_ia.core.excecoes import ProvedorIndisponivelError
from mestre_ia.core.logging_estruturado import obter_logger, LoggerComContexto


logger = LoggerComContexto(obter_logger("aplicacao.orquestrador"))


class Orquestrador:
    """Orquestrador de IA — Versão 1.0."""

    def __init__(
        self,
        provedores: Dict[str, IAProviderPort],
        capacidades: RegistroCapacidades,
    ):
        self._provedores = provedores
        self._capacidades = capacidades

    async def processar(
        self,
        requisicao: RequisicaoIA,
        timeout_ms: Optional[int] = None,
    ) -> RespostaIA:
        """Processa uma requisição encaminhando ao provedor adequado."""
        dominio = self._extrair_dominio(requisicao)

        logger.debug(
            "Processando requisição",
            requisicao_id=requisicao.id,
            dominio=dominio.value,
        )

        provedor = self._selecionar_provedor(dominio)

        if provedor is None:
            logger.error(
                "Nenhum provedor compatível encontrado",
                dominio=dominio.value,
                provedores_disponiveis=list(self._provedores.keys()),
            )
            raise ProvedorIndisponivelError(
                provedor="todos",
                tentativa=0,
            )

        kwargs = {}
        if timeout_ms is not None:
            kwargs["timeout_ms"] = timeout_ms

        logger.info(
            "Encaminhando requisição",
            requisicao_id=requisicao.id,
            provedor=str(provedor.provedor),
        )

        return await provedor.enviar_prompt(requisicao, **kwargs)

    async def processar_streaming(
        self,
        requisicao: RequisicaoIA,
        timeout_ms: Optional[int] = None,
    ):
        """Processa uma requisição em modo streaming."""
        dominio = self._extrair_dominio(requisicao)
        provedor = self._selecionar_provedor(dominio)

        if provedor is None:
            raise ProvedorIndisponivelError(
                provedor="todos",
                tentativa=0,
            )

        kwargs = {}
        if timeout_ms is not None:
            kwargs["timeout_ms"] = timeout_ms

        async for fragmento in provedor.enviar_prompt_streaming(
            requisicao,
            **kwargs,
        ):
            yield fragmento

    def _extrair_dominio(
        self,
        requisicao: RequisicaoIA,
    ) -> DominioTarefa:
        """Extrai o domínio da tarefa dos metadados."""
        dominio_str = requisicao.metadados.get(
            "dominio",
            "conversacao",
        )

        try:
            return DominioTarefa(dominio_str)
        except ValueError:
            logger.debug(
                "Domínio não reconhecido, usando CONVERSACAO",
                dominio_informado=dominio_str,
            )
            return DominioTarefa.CONVERSACAO

    def _selecionar_provedor(
        self,
        dominio: DominioTarefa,
    ) -> Optional[IAProviderPort]:
        """Seleciona o provedor compatível para o domínio."""
        perfis = self._capacidades.buscar_por_dominio(dominio)

        for perfil in perfis:
            provedor = self._provedores.get(perfil.provedor)

            if provedor is not None:
                logger.debug(
                    "Provedor selecionado",
                    provedor=perfil.provedor,
                    modelo=perfil.modelo,
                    dominio=dominio.value,
                )
                return provedor

        if self._provedores:
            primeiro = list(self._provedores.values())[0]

            logger.debug(
                "Usando provedor padrão",
                provedor=str(primeiro.provedor),
            )

            return primeiro

        return None