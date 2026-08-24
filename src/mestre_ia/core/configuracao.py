"""
Sistema de Configuração Hierárquica — Projeto Orion.

Princípios:
1. Configuração explícita > Configuração implícita
2. Ambiente > Arquivo .env.[ambiente] > .env > Default
3. Tipagem forte: toda configuração tem tipo definido
4. Validação na carga: falha rápido se configuração for inválida
5. Imutável após carga: evita efeitos colaterais

Precedência exata (a última sobrescreve as anteriores):
1. Valores padrão (definidos nas dataclasses)
2. Arquivo config.toml (se existir)
3. Arquivo .env (se existir)
4. Arquivo .env.<ambiente> (se existir)
5. Variáveis de ambiente do sistema operacional (MESTRE_IA_*)

Variáveis sem o prefixo MESTRE_IA_ (ex.: DEEPSEEK_API_KEY) também são
capturadas e armazenadas na estrutura apropriada (ConfiguracaoIA.provedores).
"""

import json
import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, get_type_hints


class Ambiente(Enum):
    """
    Ambientes de execução suportados.

    Cada ambiente pode ter configurações diferentes:
    - DESENVOLVIMENTO: Logging verboso, hot reload, debug
    - HOMOLOGACAO: Similar a produção, dados anonimizados
    - PRODUCAO: Máxima segurança, logging mínimo, otimizado
    - TESTE: Banco em memória, mocks ativados
    """

    DESENVOLVIMENTO = "dev"
    HOMOLOGACAO = "homolog"
    PRODUCAO = "prod"
    TESTE = "teste"

    @classmethod
    def detectar(cls) -> "Ambiente":
        """
        Detecta automaticamente o ambiente atual.

        Ordem de detecção:
        1. Variável MESTRE_IA_AMBIENTE
        2. Variável ENVIRONMENT (padrão Docker)
        3. Default: DESENVOLVIMENTO
        """
        valor = os.getenv("MESTRE_IA_AMBIENTE") or os.getenv("ENVIRONMENT", "dev")
        try:
            return cls(valor.lower())
        except ValueError:
            return cls.DESENVOLVIMENTO


@dataclass(frozen=True, kw_only=True)
class ConfiguracaoLogging:
    """Configuração do sistema de logging."""

    nivel: str = "INFO"
    formato: str = "json"
    destino: str = "stdout"
    arquivo_log: Optional[str] = None
    sentry_dsn: Optional[str] = None

    def __post_init__(self):
        niveis_validos = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.nivel.upper() not in niveis_validos:
            raise ValueError(
                f"Nível de log inválido: '{self.nivel}'. Use: {niveis_validos}"
            )
        if self.formato not in ("json", "texto"):
            raise ValueError(
                f"Formato de log inválido: '{self.formato}'. Use: json, texto"
            )


@dataclass(frozen=True, kw_only=True)
class ConfiguracaoIA:
    """Configuração para provedores de IA."""

    provedor_padrao: str = "deepseek"
    timeout_ms: int = 30000
    max_retries: int = 3
    backoff_inicial_ms: int = 1000
    backoff_maximo_ms: int = 30000
    cache_habilitado: bool = True
    cache_ttl_segundos: int = 3600
    provedores: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def __post_init__(self):
        if self.timeout_ms <= 0:
            raise ValueError("timeout_ms deve ser maior que zero.")
        if self.max_retries < 0:
            raise ValueError("max_retries não pode ser negativo.")
        if self.backoff_inicial_ms <= 0:
            raise ValueError("backoff_inicial_ms deve ser maior que zero.")
        if self.backoff_maximo_ms <= 0:
            raise ValueError("backoff_maximo_ms deve ser maior que zero.")


@dataclass(frozen=True, kw_only=True)
class ConfiguracaoQuantum:
    """Configuração para computação quântica."""

    backend_padrao: str = "simulador"
    shots_padrao: int = 1024
    simulador_max_qubits: int = 32
    ibm_token: Optional[str] = None
    origin_token: Optional[str] = None

    def __post_init__(self):
        if self.shots_padrao <= 0:
            raise ValueError("shots_padrao deve ser maior que zero.")
        if self.simulador_max_qubits <= 0:
            raise ValueError("simulador_max_qubits deve ser maior que zero.")


@dataclass(frozen=True, kw_only=True)
class ConfiguracaoMemoria:
    """Configuração da camada de memória."""

    tipo_vetorial: str = "chromadb"
    dimensao_embeddings: int = 1536
    max_documentos_cache: int = 1000
    similaridade_threshold: float = 0.7

    def __post_init__(self):
        if self.dimensao_embeddings <= 0:
            raise ValueError("dimensao_embeddings deve ser maior que zero.")
        if self.max_documentos_cache <= 0:
            raise ValueError("max_documentos_cache deve ser maior que zero.")
        if not 0.0 <= self.similaridade_threshold <= 1.0:
            raise ValueError("similaridade_threshold deve estar entre 0.0 e 1.0.")


@dataclass(frozen=True, kw_only=True)
class ConfiguracaoSeguranca:
    """Configuração de segurança."""

    jwt_secret: Optional[str] = None
    jwt_algoritmo: str = "HS256"
    jwt_expiracao_minutos: int = 60
    mfa_habilitado: bool = False
    max_tentativas_login: int = 5
    bloqueio_tentativas_minutos: int = 15

    def __post_init__(self):
        if self.jwt_expiracao_minutos <= 0:
            raise ValueError("jwt_expiracao_minutos deve ser maior que zero.")
        if self.max_tentativas_login <= 0:
            raise ValueError("max_tentativas_login deve ser maior que zero.")
        if self.bloqueio_tentativas_minutos <= 0:
            raise ValueError("bloqueio_tentativas_minutos deve ser maior que zero.")


@dataclass(frozen=True, kw_only=True)
class Configuracao:
    """
    Configuração raiz — agrega todas as subconfigurações.

    Imutável após criação. Use Configuracao.carregar() para criar.
    """

    ambiente: Ambiente = field(default_factory=Ambiente.detectar)
    debug: bool = False
    logging: ConfiguracaoLogging = field(default_factory=ConfiguracaoLogging)
    ia: ConfiguracaoIA = field(default_factory=ConfiguracaoIA)
    quantum: ConfiguracaoQuantum = field(default_factory=ConfiguracaoQuantum)
    memoria: ConfiguracaoMemoria = field(default_factory=ConfiguracaoMemoria)
    seguranca: ConfiguracaoSeguranca = field(default_factory=ConfiguracaoSeguranca)
    plugins_habilitados: List[str] = field(default_factory=list)

    @classmethod
    def carregar(
        cls,
        caminho_env: Optional[Path] = None,
        caminho_toml: Optional[Path] = None,
    ) -> "Configuracao":
        """
        Fábrica principal: carrega configuração de múltiplas fontes.

        Args:
            caminho_env: Caminho para arquivo .env (default: raiz do projeto)
            caminho_toml: Caminho para config.toml (default: raiz do projeto)

        Returns:
            Configuracao imutável e validada

        Raises:
            ValueError: Se valores obrigatórios forem inválidos
        """
        config_dict: Dict[str, Any] = {}

        if caminho_toml and caminho_toml.exists():
            with open(caminho_toml, "rb") as f:
                config_dict.update(tomllib.load(f))

        if caminho_env and caminho_env.exists():
            config_dict.update(cls._carregar_dotenv(caminho_env))
        else:
            env_path = Path(".env")
            if env_path.exists():
                config_dict.update(cls._carregar_dotenv(env_path))

        ambiente_valor = config_dict.get(
            "ambiente", os.getenv("MESTRE_IA_AMBIENTE", "dev")
        )
        if isinstance(ambiente_valor, Ambiente):
            ambiente_valor = ambiente_valor.value
        env_ambiente = Path(f".env.{ambiente_valor}")
        if env_ambiente.exists():
            config_dict.update(cls._carregar_dotenv(env_ambiente))

        config_dict.update(cls._carregar_ambiente())

        cls._capturar_variaveis_provedores(config_dict)

        return cls._construir_de_dict(config_dict)

    @staticmethod
    def _carregar_dotenv(caminho: Path) -> Dict[str, Any]:
        """
        Carrega arquivo .env manualmente.

        Formato esperado:
        MESTRE_IA_DEBUG=true
        DEEPSEEK_API_KEY=sk-...

        Returns:
            Dicionário com chaves normalizadas (prefixo MESTRE_IA_ removido)
        """
        resultado: Dict[str, Any] = {}
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                if "=" not in linha:
                    continue
                chave, _, valor = linha.partition("=")
                chave = chave.strip()
                valor = valor.strip().strip('"').strip("'")
                resultado[chave] = valor
        return Configuracao._normalizar_chaves(resultado)

    @staticmethod
    def _normalizar_chaves(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Remove o prefixo MESTRE_IA_ das chaves, preservando as demais."""
        resultado: Dict[str, Any] = {}
        prefixo = "MESTRE_IA_"
        for chave, valor in raw.items():
            if chave.upper().startswith(prefixo):
                chave_limpa = chave[len(prefixo):].lower()
                resultado[chave_limpa] = valor
            else:
                resultado[chave.lower()] = valor
        return resultado

    @staticmethod
    def _carregar_ambiente() -> Dict[str, Any]:
        """
        Carrega configurações de variáveis de ambiente do sistema.

        Apenas variáveis com prefixo MESTRE_IA_ são processadas aqui.
        As variáveis sem prefixo são tratadas separadamente.
        """
        resultado: Dict[str, Any] = {}
        prefixo = "MESTRE_IA_"

        for chave, valor in os.environ.items():
            if not chave.upper().startswith(prefixo):
                continue

            chave_limpa = chave[len(prefixo):].lower()
            partes = chave_limpa.split("_")

            if len(partes) == 1:
                resultado[partes[0]] = Configuracao._converter_tipo(valor)
            else:
                secao = partes[0]
                campo = "_".join(partes[1:])
                if secao not in resultado:
                    resultado[secao] = {}
                resultado[secao][campo] = Configuracao._converter_tipo(valor)

        return resultado

    @staticmethod
    def _capturar_variaveis_provedores(config_dict: Dict[str, Any]) -> None:
        """
        Captura variáveis de ambiente sem prefixo MESTRE_IA_ que são chaves de
        provedores (ex.: DEEPSEEK_API_KEY) e as insere em config.ia.provedores.
        A precedência correta é: sistema sobrescreve .env.
        """
        provedores: Dict[str, Dict[str, str]] = {}

        provedor_por_prefixo = {
            "DEEPSEEK": "deepseek",
            "OPENAI": "openai",
            "GEMINI": "gemini",
            "MISTRAL": "mistral",
            "KIMI": "kimi",
            "QWEN": "qwen",
        }

        for chave, valor in config_dict.items():
            if not isinstance(valor, str):
                continue
            for prefixo, provedor in provedor_por_prefixo.items():
                if chave.upper().startswith(prefixo):
                    if provedor not in provedores:
                        provedores[provedor] = {}
                    campo = chave[len(prefixo) + 1:].lower()
                    provedores[provedor][campo] = valor
                    break

        for chave, valor in os.environ.items():
            for prefixo, provedor in provedor_por_prefixo.items():
                if chave.upper().startswith(prefixo):
                    if provedor not in provedores:
                        provedores[provedor] = {}
                    campo = chave[len(prefixo) + 1:].lower()
                    provedores[provedor][campo] = valor
                    break

        if provedores:
            config_dict.setdefault("ia", {})
            if not isinstance(config_dict["ia"], dict):
                config_dict["ia"] = {}
            existentes = config_dict["ia"].get("provedores", {})
            if isinstance(existentes, dict):
                for prov, cfg in provedores.items():
                    if prov not in existentes:
                        existentes[prov] = {}
                    existentes[prov].update(cfg)
                config_dict["ia"]["provedores"] = existentes
            else:
                config_dict["ia"]["provedores"] = provedores

    @staticmethod
    def _converter_tipo(valor: str) -> Any:
        """
        Converte string para tipo Python apropriado.

        "true" → True
        "false" → False
        "123" → 123
        "3.14" → 3.14
        "[1,2,3]" → [1, 2, 3]
        resto → string
        """
        if not isinstance(valor, str):
            return valor

        valor_lower = valor.lower().strip()

        if valor_lower in ("true", "yes", "1"):
            return True
        if valor_lower in ("false", "no", "0"):
            return False

        try:
            return int(valor)
        except ValueError:
            pass

        try:
            return float(valor)
        except ValueError:
            pass

        if (valor.startswith("[") and valor.endswith("]")) or (
            valor.startswith("{") and valor.endswith("}")
        ):
            try:
                return json.loads(valor)
            except json.JSONDecodeError:
                pass

        return valor

    @classmethod
    def _construir_de_dict(cls, dados: Dict[str, Any]) -> "Configuracao":
        """
        Constrói instância tipada de Configuracao a partir de dicionário.
        """
        kwargs: Dict[str, Any] = {}

        for nome_campo, tipo_campo in get_type_hints(cls).items():
            if nome_campo in dados:
                valor = dados[nome_campo]
                if hasattr(tipo_campo, "__dataclass_fields__"):
                    if isinstance(valor, dict):
                        kwargs[nome_campo] = tipo_campo(**valor)
                    else:
                        kwargs[nome_campo] = valor
                else:
                    kwargs[nome_campo] = valor

        if "ambiente" in dados:
            amb = dados["ambiente"]
            if isinstance(amb, str):
                kwargs["ambiente"] = Ambiente(amb.lower())
            elif isinstance(amb, Ambiente):
                kwargs["ambiente"] = amb

        return cls(**kwargs)

    def para_dict_seguro(self) -> Dict[str, Any]:
        """
        Serializa a configuração ocultando valores sensíveis.

        Tokens, API keys e segredos são OMITIDOS intencionalmente.
        """
        resultado: Dict[str, Any] = {
            "ambiente": self.ambiente.value,
            "debug": self.debug,
            "logging": {
                "nivel": self.logging.nivel,
                "formato": self.logging.formato,
                "destino": self.logging.destino,
            },
            "ia": {
                "provedor_padrao": self.ia.provedor_padrao,
                "timeout_ms": self.ia.timeout_ms,
                "max_retries": self.ia.max_retries,
                "cache_habilitado": self.ia.cache_habilitado,
                "provedores": {
                    nome: {k: v for k, v in cfg.items() if "key" not in k.lower() and "token" not in k.lower() and "secret" not in k.lower()}
                    for nome, cfg in self.ia.provedores.items()
                },
            },
            "memoria": {
                "tipo_vetorial": self.memoria.tipo_vetorial,
                "dimensao_embeddings": self.memoria.dimensao_embeddings,
            },
            "seguranca": {
                "jwt_algoritmo": self.seguranca.jwt_algoritmo,
                "mfa_habilitado": self.seguranca.mfa_habilitado,
            },
        }
        return resultado
