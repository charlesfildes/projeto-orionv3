"""
Hierarquia de exceções do Projeto Orion (mestre_ia).

Princípios:
1. Exceções específicas > Exceções genéricas
2. Toda exceção carrega contexto suficiente para debugging
3. Exceções de domínio são distintas de exceções técnicas
4. Mensagens em português (domínio médico brasileiro)
5. Segurança: contexto nunca expõe segredos em logs ou serializações
"""

import re
from typing import Any, Dict, Optional
from datetime import datetime, timezone


# ============================================================================
# EXCEÇÕES BASE
# ============================================================================

class MestreIAError(Exception):
    """
    Exceção base para todo o projeto.

    Toda exceção do Mestre-IA deve herdar desta classe.
    Isso permite capturar todas as exceções do sistema com um único except.

    Atributos:
        mensagem: Descrição legível do erro
        codigo: Código único para identificação programática
        contexto: Dicionário com informações de debug
        timestamp: Momento da exceção (UTC)
    """

    _PADROES_SENSIVEIS = re.compile(
        r'(sk-[a-zA-Z0-9]+)'
        r'|(Bearer\s+[a-zA-Z0-9\-_\.]+)'
        r'|(api_key=[a-zA-Z0-9]+)'
        r'|(secret=[a-zA-Z0-9]+)'
        r'|(password=[^\s,]+)'
        r'|(token=[a-zA-Z0-9\-_\.]+)'
    )

    def __init__(
        self,
        mensagem: str,
        codigo: Optional[str] = None,
        contexto: Optional[Dict[str, Any]] = None
    ):
        self.mensagem = mensagem
        self.codigo = codigo or self.__class__.__name__
        self.contexto = contexto or {}
        self.timestamp = datetime.now(timezone.utc)
        super().__init__(mensagem)

    def __str__(self) -> str:
        """Representação segura para logging (sem segredos)."""
        partes = [f"[{self.codigo}] {self.mensagem}"]
        contexto_seguro = self._contexto_seguro()
        if contexto_seguro:
            partes.append(f"Contexto: {contexto_seguro}")
        return " | ".join(partes)

    def para_dict(self) -> Dict[str, Any]:
        """
        Serializa para JSON (útil em APIs).
        Não inclui valores sensíveis no contexto.
        """
        return {
            "erro": self.codigo,
            "mensagem": self.mensagem,
            "timestamp": self.timestamp.isoformat(),
            "contexto": self._contexto_seguro()
        }

    def _contexto_seguro(self) -> Dict[str, Any]:
        """
        Retorna uma cópia do contexto com valores sensíveis mascarados.
        """
        return {
            chave: self._sanitizar_valor(valor)
            for chave, valor in self.contexto.items()
        }

    @classmethod
    def _sanitizar_valor(cls, valor: Any) -> Any:
        """
        Substitui padrões sensíveis por [REDACTED] em strings.
        Para outros tipos, retorna o valor original.
        """
        if isinstance(valor, str):
            return cls._PADROES_SENSIVEIS.sub('[REDACTED]', valor)
        elif isinstance(valor, dict):
            return {k: cls._sanitizar_valor(v) for k, v in valor.items()}
        elif isinstance(valor, list):
            return [cls._sanitizar_valor(item) for item in valor]
        return valor


class ErroDominio(MestreIAError):
    """
    Exceção base para erros de regra de negócio.

    Erros de domínio representam violações de regras de negócio.
    Ex: diagnosticar paciente sem sintomas, nível de evidência inválido.

    Estes erros são ESPERADOS e devem ser tratados com mensagens amigáveis.
    """
    pass


class ErroInfraestrutura(MestreIAError):
    """
    Exceção base para erros de infraestrutura.

    Erros de infraestrutura representam falhas técnicas externas.
    Ex: API indisponível, banco de dados offline, timeout.

    Estes erros são INESPERADOS e devem acionar retry/fallback.
    """
    pass


class ErroConfiguracao(MestreIAError):
    """
    Erro de configuração do sistema.

    Falha na inicialização: variáveis obrigatórias ausentes,
    arquivos de config inválidos, valores fora do domínio.

    Deve ser lançado na inicialização (fail-fast).
    """
    pass


class ErroSeguranca(MestreIAError):
    """
    Violação de segurança.

    Token inválido, permissão insuficiente, tentativa de acesso não autorizado.
    Deve ser logado com severidade máxima e potencialmente gerar alertas.
    """
    pass


# ============================================================================
# EXCEÇÕES DE DOMÍNIO ESPECÍFICAS
# ============================================================================

class PacienteSemSintomasError(ErroDominio):
    """Tentativa de diagnóstico sem sintomas."""

    def __init__(self, paciente_id: str):
        super().__init__(
            mensagem="Não é possível gerar diagnóstico: paciente não possui sintomas registrados.",
            codigo="PACIENTE_SEM_SINTOMAS",
            contexto={"paciente_id": paciente_id}
        )


class EvidenciaInvalidaError(ErroDominio):
    """Evidência não atende aos critérios de validação."""

    def __init__(self, motivo: str, afirmacao: str):
        super().__init__(
            mensagem=f"Evidência inválida: {motivo}",
            codigo="EVIDENCIA_INVALIDA",
            contexto={"afirmacao": afirmacao[:100]}
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
                "motivo": motivo
            }
        )


class ReferenciaInvalidaError(ErroDominio):
    """Referência científica não atende aos padrões."""

    def __init__(self, campo: str, valor: str, motivo: str):
        super().__init__(
            mensagem=f"Referência inválida no campo '{campo}': {motivo}",
            codigo="REFERENCIA_INVALIDA",
            contexto={"campo": campo, "valor": valor}
        )


# ============================================================================
# EXCEÇÕES DE INFRAESTRUTURA
# ============================================================================

class ProvedorIndisponivelError(ErroInfraestrutura):
    """Provedor de IA está offline ou inacessível."""

    def __init__(self, provedor: str, tentativa: int = 0):
        super().__init__(
            mensagem=f"Provedor '{provedor}' indisponível após {tentativa} tentativas.",
            codigo="PROVEDOR_INDISPONIVEL",
            contexto={"provedor": provedor, "tentativas": tentativa}
        )


class LimiteExcedidoError(ErroInfraestrutura):
    """Rate limit ou cota excedida no provedor."""

    def __init__(self, provedor: str, retry_after_segundos: Optional[int] = None):
        contexto = {"provedor": provedor}
        if retry_after_segundos:
            contexto["retry_after_segundos"] = retry_after_segundos

        super().__init__(
            mensagem=f"Limite excedido no provedor '{provedor}'."
                     f"{' Tentar novamente em ' + str(retry_after_segundos) + 's' if retry_after_segundos else ''}",
            codigo="LIMITE_EXCEDIDO",
            contexto=contexto
        )


class TokenInvalidoError(ErroInfraestrutura):
    """Token de API inválido ou expirado."""

    def __init__(self, provedor: str):
        super().__init__(
            mensagem=f"Token inválido ou expirado para '{provedor}'. Verifique sua API key.",
            codigo="TOKEN_INVALIDO",
            contexto={"provedor": provedor}
        )


class RespostaInesperadaError(ErroInfraestrutura):
    """Resposta do provedor não segue o formato esperado."""

    def __init__(self, provedor: str, detalhe: str, resposta_bruta: str = ""):
        sanitizada = MestreIAError._sanitizar_valor(resposta_bruta)[:200]
        super().__init__(
            mensagem=f"Resposta inesperada de '{provedor}': {detalhe}",
            codigo="RESPOSTA_INESPERADA",
            contexto={
                "provedor": provedor,
                "detalhe": detalhe,
                "resposta_truncada": sanitizada
            }
        )


class TimeoutExcedidoError(ErroInfraestrutura):
    """Timeout ao aguardar resposta do provedor."""

    def __init__(self, provedor: str, timeout_ms: int):
        super().__init__(
            mensagem=f"Timeout de {timeout_ms}ms excedido para '{provedor}'.",
            codigo="TIMEOUT_EXCEDIDO",
            contexto={"provedor": provedor, "timeout_ms": timeout_ms}
        )


# ============================================================================
# EXCEÇÕES DE CONFIGURAÇÃO
# ============================================================================

class ConfiguracaoAusenteError(ErroConfiguracao):
    """Configuração obrigatória não encontrada."""

    def __init__(self, chave: str):
        super().__init__(
            mensagem=f"Configuração obrigatória ausente: '{chave}'. "
                     f"Defina a variável de ambiente MESTRE_IA_{chave.upper()} "
                     f"ou adicione ao arquivo .env",
            codigo="CONFIG_AUSENTE",
            contexto={"chave": chave}
        )


class ConfiguracaoInvalidaError(ErroConfiguracao):
    """Valor de configuração fora do domínio esperado."""

    def __init__(self, chave: str, valor: str, esperado: str):
        super().__init__(
            mensagem=f"Valor inválido para '{chave}': '{valor}'. Esperado: {esperado}",
            codigo="CONFIG_INVALIDA",
            contexto={"chave": chave, "valor": valor, "esperado": esperado}
        )
