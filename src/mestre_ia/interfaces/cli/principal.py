"""
CLI Principal do Projeto Orion — Mestre-IA v1.0.

Comandos:
    mestre-ia conversar       Chat interativo
    mestre-ia perguntar       Pergunta única
    mestre-ia diagnosticar    Diagnóstico diferencial

Esta versão foi refatorada para melhorar testabilidade:
- Funções menores com responsabilidade única
- Dependências injetáveis (orquestrador, memória)
- Tratamento de erros centralizado
"""

import asyncio
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from mestre_ia.core.configuracao import Configuracao
from mestre_ia.core.capacidades import RegistroCapacidades
from mestre_ia.core.contratos import RequisicaoIA, RespostaIA
from mestre_ia.core.excecoes import (
    MestreIAError,
    ProvedorIndisponivelError,
    TokenInvalidoError,
    LimiteExcedidoError,
    TimeoutExcedidoError,
    RespostaInesperadaError,
    ConfiguracaoAusenteError,
    ConfiguracaoInvalidaError,
)
from mestre_ia.core.logging_estruturado import obter_logger
from mestre_ia.infraestrutura.adaptadores.deepseek import DeepSeekAdapter
from mestre_ia.aplicacao.orquestrador import Orquestrador
from mestre_ia.memoria.curto_prazo import MemoriaCurtoPrazo
from mestre_ia.memoria.embeddings import GeradorEmbeddings
from mestre_ia.memoria.vetorial import ArmazenamentoVetorial
from mestre_ia.memoria.semantica import MemoriaSemantica

app = typer.Typer(
    name="mestre-ia",
    help="Projeto Orion — Plataforma Mestre-IA",
    add_completion=False,
)

console = Console()
logger = obter_logger("interfaces.cli")


# ============================================================================
# FACTORIES (Testáveis isoladamente)
# ============================================================================

def criar_orquestrador() -> Orquestrador:
    """
    Factory do Orquestrador com configuração do ambiente.

    Returns:
        Orquestrador configurado

    Raises:
        ConfiguracaoAusenteError: Se API key não configurada
    """
    config = Configuracao.carregar()

    deepseek_config = config.ia.provedores.get("deepseek", {})
    api_key = deepseek_config.get("api_key", "")

    if not api_key:
        raise ConfiguracaoAusenteError("DEEPSEEK_API_KEY")

    modelo_padrao = deepseek_config.get("modelo_padrao", "deepseek-chat")

    registro = RegistroCapacidades()
    adaptador = DeepSeekAdapter(
        api_key=api_key,
        modelo_padrao=modelo_padrao,
        registro_capacidades=registro,
        timeout_ms=config.ia.timeout_ms,
    )

    return Orquestrador(
        provedores={"deepseek": adaptador},
        capacidades=registro,
    )


def criar_memoria_semantica() -> MemoriaSemantica:
    """
    Factory da Memória Semântica.

    Returns:
        MemoriaSemantica configurada com embeddings fake
    """
    config = Configuracao.carregar()

    gerador = GeradorEmbeddings(modo_fake=True)

    armazenamento = ArmazenamentoVetorial(
        dimensao=gerador.dimensao,
        threshold=config.memoria.similaridade_threshold,
    )

    return MemoriaSemantica(gerador, armazenamento)


# ============================================================================
# HELPERS PURES (Altamente testáveis)
# ============================================================================

def combinar_contexto(
    contexto_usuario: Optional[str],
    contexto_semantico: Optional[str],
) -> Optional[str]:
    """
    Combina contexto do usuário com contexto semântico.

    Precedência:
    - Nenhum: None
    - Apenas um: retorna ele
    - Ambos: contexto_usuario + "\\n\\n" + contexto_semantico
    """
    if not contexto_usuario and not contexto_semantico:
        return None
    if contexto_usuario and not contexto_semantico:
        return contexto_usuario
    if not contexto_usuario and contexto_semantico:
        return contexto_semantico
    return f"{contexto_usuario}\n\n{contexto_semantico}"


def mesclar_metadados(
    metadados_existentes: Optional[Dict] = None,
    **novos: Any,
) -> Dict[str, Any]:
    """
    Mescla metadados existentes com novos campos.
    Nunca modifica o dicionário original.
    """
    resultado = dict(metadados_existentes or {})
    resultado.update(novos)
    return resultado


# ============================================================================
# EXIBIÇÃO E ERROS
# ============================================================================

def exibir_resposta(resposta: RespostaIA) -> None:
    """Exibe resposta formatada."""
    console.print(Markdown(resposta.conteudo))
    console.print(
        f"[dim]({resposta.modelo} | "
        f"{resposta.tokens_entrada}+{resposta.tokens_saida} tokens | "
        f"{resposta.tempo_resposta_ms:.0f}ms)[/dim]"
    )


def tratar_erro(erro: Exception) -> None:
    """Exibe erro amigável ao usuário, sem stack trace."""
    if isinstance(erro, TokenInvalidoError):
        console.print("[red]Erro de autenticação.[/red] Verifique sua API key do DeepSeek.")
        console.print("[dim]Acesse https://platform.deepseek.com/ para obter uma chave.[/dim]")
    elif isinstance(erro, LimiteExcedidoError):
        console.print("[yellow]Limite de requisições excedido.[/yellow] Aguarde alguns instantes.")
    elif isinstance(erro, TimeoutExcedidoError):
        console.print("[yellow]Timeout.[/yellow] O servidor demorou muito para responder.")
    elif isinstance(erro, ProvedorIndisponivelError):
        console.print("[red]Serviço indisponível.[/red] Verifique sua conexão ou tente novamente.")
    elif isinstance(erro, ConfiguracaoAusenteError):
        console.print("[red]Configuração ausente.[/red] Execute 'cp .env.example .env' e configure sua API key.")
    elif isinstance(erro, ConfiguracaoInvalidaError):
        console.print(f"[red]Configuração inválida:[/red] {erro.mensagem}")
    elif isinstance(erro, RespostaInesperadaError):
        console.print("[red]Resposta inesperada do servidor.[/red] Tente novamente.")
    elif isinstance(erro, MestreIAError):
        console.print(f"[red]Erro:[/red] {erro.mensagem}")
    else:
        console.print(f"[red]Erro inesperado:[/red] {type(erro).__name__}")


# ============================================================================
# PROCESSAMENTO DE MENSAGEM
# ============================================================================

async def processar_mensagem(
    prompt: str,
    memoria: MemoriaCurtoPrazo,
    orquestrador: Orquestrador,
    memoria_semantica: MemoriaSemantica,
    modo_streaming: bool = False,
) -> Optional[RespostaIA]:
    """
    Processa uma mensagem do usuário com enriquecimento semântico.

    Returns:
        RespostaIA se não-streaming, None se streaming
    """
    contexto_sem = await memoria_semantica.buscar_contexto(prompt)
    contexto_final = combinar_contexto(
        None,
        contexto_sem
    )

    metadados = mesclar_metadados(
        contexto_recuperado=(contexto_sem is not None)
    )

    historico = memoria.obter_historico()

    requisicao = RequisicaoIA(
        prompt=prompt,
        contexto_sistema=contexto_final,
        historico=historico,
        metadados=metadados,
    )

    if modo_streaming:
        console.print("[bold cyan]Orion →[/bold cyan] ", end="")
        resposta_completa = ""
        async for fragmento in orquestrador.processar_streaming(requisicao):
            console.print(fragmento, end="", highlight=False)
            resposta_completa += fragmento
        console.print()
        console.print("[dim](streaming)[/dim]")
        memoria.adicionar(prompt, resposta_completa)
        return None

    resposta = await orquestrador.processar(requisicao)
    console.print("[bold cyan]Orion →[/bold cyan] ", end="")
    exibir_resposta(resposta)
    memoria.adicionar(prompt, resposta.conteudo)
    return resposta


# ============================================================================
# COMANDOS DA CLI
# ============================================================================

@app.command()
def conversar():
    """Inicia chat interativo com o Orion."""
    console.print(Panel.fit(
        "[bold cyan]Projeto Orion — Mestre-IA v1.0[/bold cyan]\n\n"
        "Digite uma mensagem ou [yellow]/ajuda[/yellow] para ver os comandos.",
        title="Bem-vindo",
        border_style="cyan",
    ))

    try:
        orquestrador = criar_orquestrador()
    except MestreIAError as e:
        tratar_erro(e)
        raise typer.Exit(code=1)

    memoria = MemoriaCurtoPrazo()
    memoria_semantica = criar_memoria_semantica()
    modo_streaming = False

    while True:
        try:
            entrada = console.input("[bold green]Você →[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Encerrando...[/dim]")
            break

        if not entrada:
            continue

        # Comandos começam com /
        if entrada.startswith("/"):
            deve_sair, modo_streaming = processar_comando(
                entrada, memoria, modo_streaming
            )
            if deve_sair:
                break
            continue

        # Palavras de ajuda sem barra
        if entrada.lower() in ("help", "--help", "-h", "ajuda"):
            exibir_ajuda()
            continue

        # Processar mensagem normal
        try:
            asyncio.run(processar_mensagem(
                entrada, memoria, orquestrador,
                memoria_semantica, modo_streaming,
            ))
        except Exception as e:
            tratar_erro(e)

    console.print("[dim]Até logo![/dim]")


@app.command()
def perguntar(prompt: str):
    """Envia uma pergunta única e exibe a resposta."""
    try:
        orquestrador = criar_orquestrador()
    except MestreIAError as e:
        tratar_erro(e)
        raise typer.Exit(code=1)

    requisicao = RequisicaoIA(prompt=prompt)

    try:
        resposta = asyncio.run(orquestrador.processar(requisicao))
    except Exception as e:
        tratar_erro(e)
        raise typer.Exit(code=1)

    exibir_resposta(resposta)


@app.command()
def diagnosticar(
    sintomas: str = typer.Option(
        ..., "--sintomas", "-s", help="Sintomas separados por vírgula"
    )
):
    """Gera diagnóstico diferencial baseado em sintomas."""
    try:
        orquestrador = criar_orquestrador()
    except MestreIAError as e:
        tratar_erro(e)
        raise typer.Exit(code=1)

    prompt = (
        f"Com base nos seguintes sintomas: {sintomas}\n\n"
        "Forneça um diagnóstico diferencial com possíveis condições, "
        "probabilidades estimadas e nível de evidência para cada uma. "
        "Diferencie claramente fatos comprovados de hipóteses."
    )

    requisicao = RequisicaoIA(
        prompt=prompt,
        metadados={"dominio": "medicina"},
    )

    try:
        resposta = asyncio.run(orquestrador.processar(requisicao))
    except Exception as e:
        tratar_erro(e)
        raise typer.Exit(code=1)

    console.print(Panel.fit(
        Markdown(resposta.conteudo),
        title="Diagnóstico Diferencial",
        border_style="blue",
    ))
    console.print(
        f"[dim]({resposta.modelo} | "
        f"{resposta.tokens_entrada}+{resposta.tokens_saida} tokens | "
        f"{resposta.tempo_resposta_ms:.0f}ms)[/dim]"
    )


# ============================================================================
# PROCESSAMENTO DE COMANDOS INTERATIVOS
# ============================================================================

def processar_comando(
    entrada: str,
    memoria: MemoriaCurtoPrazo,
    modo_streaming: bool,
) -> tuple:
    """
    Processa comandos iniciados com /.

    Returns:
        (deve_sair: bool, modo_streaming: bool)
    """
    partes = entrada.split(maxsplit=1)
    comando = partes[0].lower()
    argumento = partes[1] if len(partes) > 1 else ""

    if comando == "/sair":
        return True, modo_streaming

    elif comando == "/ajuda":
        exibir_ajuda()

    elif comando == "/status":
        exibir_status(memoria, modo_streaming)

    elif comando == "/stream":
        modo_streaming = not modo_streaming
        estado = "ATIVADO" if modo_streaming else "DESATIVADO"
        console.print(f"Streaming {estado}")

    elif comando == "/contexto":
        if argumento:
            memoria.contexto_sistema = argumento
            console.print(f"Contexto definido: [italic]{argumento}[/italic]")
        else:
            memoria.contexto_sistema = None
            console.print("Contexto removido")

    elif comando == "/limpar":
        memoria.limpar()
        console.print("Histórico limpo (contexto preservado)")

    else:
        console.print(f"[yellow]Comando desconhecido: {comando}[/yellow]")
        console.print("Digite [yellow]/ajuda[/yellow] para ver os comandos disponíveis.")

    return False, modo_streaming


def exibir_ajuda() -> None:
    """Exibe lista de comandos."""
    table = Table(title="Comandos Disponíveis", border_style="cyan")
    table.add_column("Comando", style="yellow")
    table.add_column("Descrição")

    table.add_row("/ajuda", "Mostra esta lista")
    table.add_row("/sair", "Encerra a conversa")
    table.add_row("/status", "Informações da sessão")
    table.add_row("/stream", "Ativa/desativa modo streaming")
    table.add_row("/contexto <texto>", "Define o contexto do sistema")
    table.add_row("/limpar", "Limpa o histórico da conversa")

    console.print(table)


def exibir_status(memoria: MemoriaCurtoPrazo, modo_streaming: bool) -> None:
    """Exibe informações da sessão."""
    console.print("Status da Sessão")
    console.print(f"   Histórico: {memoria.total_mensagens} mensagens")
    console.print(f"   Contexto: {'Definido' if memoria.contexto_sistema else 'Não definido'}")
    console.print(f"   Streaming: {'Ativo' if modo_streaming else 'Inativo'}")


if __name__ == "__main__":
    app()
