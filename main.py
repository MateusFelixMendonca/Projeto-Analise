"""
Ponto de Entrada Principal (main.py)
-----------------------------------
Interface de linha de comando (CLI) para execução das três etapas do projeto:
1. python main.py processar — Processa os vídeos listados em videos.csv e grava as métricas.
2. python main.py indice    — Normaliza as métricas e calcula o índice de estimulação (0 a 1).
3. python main.py comparar  — Gera tabela estatística e gráficos comparativos por grupo.
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import banco
import comparacao
import config
import indice
import metricas


def comando_processar(args: argparse.Namespace) -> None:
    """
    Lê o arquivo 'videos.csv' e, para cada vídeo encontrado na pasta 'videos/':
    - Verifica se já foi processado no banco (se sim, pula para economizar tempo).
    - Executa o cálculo das métricas de processamento de imagens.
    - Mede o tempo de processamento com time.perf_counter.
    - Salva os resultados no banco SQLite.
    """
    banco.criar_tabelas()

    caminho_csv = Path(config.ARQUIVO_CSV_VIDEOS)
    if not caminho_csv.is_file():
        print(f"Erro: O arquivo de metadados '{config.ARQUIVO_CSV_VIDEOS}' não foi encontrado.")
        print("Crie o arquivo com as colunas: arquivo,grupo,fonte,link")
        return

    pasta_videos = config.DIRETORIO_VIDEOS
    if not pasta_videos.is_dir():
        pasta_videos.mkdir(parents=True, exist_ok=True)

    with open(caminho_csv, mode="r", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        linhas = list(leitor)

    if not linhas:
        print(f"Aviso: O arquivo '{config.ARQUIVO_CSV_VIDEOS}' está vazio ou não possui registros válidos.")
        return

    print(f"\nIniciando processamento de {len(linhas)} vídeos listados em '{config.ARQUIVO_CSV_VIDEOS}'...")
    print("-" * 75)

    processados_agora = 0
    pulados = 0
    erros = 0

    for idx, item in enumerate(linhas, start=1):
        nome_arquivo = item.get("arquivo", "").strip()
        grupo = item.get("grupo", "").strip().lower()
        fonte = item.get("fonte", "").strip()
        link = item.get("link", "").strip()

        if not nome_arquivo:
            print(f"[{idx}/{len(linhas)}] Registro ignorado: nome de arquivo em branco no CSV.")
            erros += 1
            continue

        caminho_arquivo = pasta_videos / nome_arquivo

        # Verifica se o vídeo já foi processado anteriormente
        metrica_existente = banco.obter_metricas_video(nome_arquivo)
        if metrica_existente is not None and not getattr(args, "reprocessar", False):
            print(f"[{idx}/{len(linhas)}] [PULADO] '{nome_arquivo}' já foi processado anteriormente.")
            pulados += 1
            continue

        # Verifica se o arquivo físico existe na pasta 'videos/'
        if not caminho_arquivo.is_file():
            print(f"[{idx}/{len(linhas)}] [AVISO] Arquivo '{caminho_arquivo}' não encontrado no disco. Pulando.")
            erros += 1
            continue

        print(f"[{idx}/{len(linhas)}] Processando '{nome_arquivo}' (Grupo: {grupo})...", end="", flush=True)

        try:
            inicio_proc = time.perf_counter()
            dados = metricas.processar_video(str(caminho_arquivo))
            tempo_total = time.perf_counter() - inicio_proc

            video_id = banco.inserir_ou_obter_video(
                arquivo=nome_arquivo,
                grupo=grupo,
                fonte=fonte,
                link=link,
                duracao_s=dados["duracao_s"],
            )

            banco.salvar_metricas(
                video_id=video_id,
                cortes_por_min=dados["cortes_por_min"],
                saturacao_media=dados["saturacao_media"],
                movimento_medio=dados["movimento_medio"],
                tempo_processamento_s=dados["tempo_processamento_s"],
            )

            processados_agora += 1
            print(
                f" Concluído em {tempo_total:.1f}s | "
                f"Cortes: {dados['cortes_por_min']:.1f}/min | "
                f"Sat: {dados['saturacao_media']:.1f}% | "
                f"Mov: {dados['movimento_medio']:.3f}"
            )

        except Exception as e:
            print(f" ERRO ao processar vídeo: {e}")
            erros += 1

    print("-" * 75)
    print(
        f"Processamento concluído. Novos processados: {processados_agora}, "
        f"Já existentes (pulados): {pulados}, Não encontrados/Erros: {erros}."
    )
    print("Próximo passo recomendado: python main.py indice\n")


def comando_indice(args: argparse.Namespace) -> None:
    """
    Executa a normalização min-max das métricas no banco de dados
    e calcula o índice de estimulação visual relativo de cada vídeo.
    """
    print("\nCalculando o Índice de Estimulação Visual relativo ao conjunto...")
    qtd = indice.recalcular_indices_banco()
    if qtd > 0:
        print("Cálculo finalizado com sucesso!")
        print("Próximo passo recomendado: python main.py comparar\n")


def comando_comparar(args: argparse.Namespace) -> None:
    """
    Gera a tabela descritiva e os gráficos comparativos entre grupos.
    """
    print("\nGerando análise comparativa e gráficos...")
    sucesso = comparacao.gerar_comparacao()
    if sucesso:
        print("Análise comparativa e gráficos gerados com sucesso na pasta 'resultados/'!\n")


def construir_parser() -> argparse.ArgumentParser:
    """
    Configura os comandos e opções da CLI usando a biblioteca padrão argparse.
    """
    parser = argparse.ArgumentParser(
        description="Estimativa Computacional da Estimulação Visual em Vídeos Curtos por Processamento de Imagens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comando a ser executado")

    # Comando: processar
    parser_proc = subparsers.add_parser(
        "processar",
        help="Processa os vídeos da pasta videos/ e armazena as métricas no banco SQLite"
    )
    parser_proc.add_argument(
        "--reprocessar",
        action="store_true",
        help="Força o reprocessamento de vídeos mesmo que já existam no banco"
    )

    # Comando: indice
    subparsers.add_parser(
        "indice",
        help="Calcula o índice de estimulação visual (0 a 1) normalizando as métricas dos vídeos"
    )

    # Comando: comparar
    subparsers.add_parser(
        "comparar",
        help="Gera relatório estatístico CSV e gráficos de barras comparando os grupos"
    )

    return parser


def main() -> None:
    parser = construir_parser()
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.comando == "processar":
        comando_processar(args)
    elif args.comando == "indice":
        comando_indice(args)
    elif args.comando == "comparar":
        comando_comparar(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
