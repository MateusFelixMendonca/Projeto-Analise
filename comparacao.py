"""
Módulo de Comparação Estatística e Visualização (comparacao.py)
--------------------------------------------------------------
Analisa os dados consolidados no banco de dados SQLite, calculando estatísticas
descritivas (média, desvio padrão, mediana) para os grupos 'alta' e 'baixa'
estimulação, gerando tabela CSV e gráficos comparativos em PNG.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List
import matplotlib
# Configura backend não-interativo para geração limpa de figuras sem janela GUI
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import banco
import config


def calcular_estatisticas_grupo(valores: List[float]) -> Dict[str, float]:
    """
    Calcula média, desvio padrão amostral e mediana de uma lista numérica.
    """
    if not valores:
        return {"n": 0, "media": 0.0, "desvio_padrao": 0.0, "mediana": 0.0}

    arr = np.array(valores, dtype=float)
    n = len(arr)
    media = float(np.mean(arr))
    desvio = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    mediana = float(np.median(arr))

    return {
        "n": n,
        "media": round(media, 2),
        "desvio_padrao": round(desvio, 2),
        "mediana": round(mediana, 2),
    }


def gerar_comparacao(
    caminho_banco: str = config.CAMINHO_BANCO,
    diretorio_saida: Path = config.DIRETORIO_RESULTADOS,
) -> bool:
    """
    Agrupa os dados por categoria ('alta' e 'baixa'), calcula as estatísticas,
    imprime a tabela no terminal, exporta para CSV e gera os gráficos PNG.
    """
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    todos = banco.listar_todos_os_resultados(caminho_banco)

    # Filtra apenas vídeos que já possuem todas as métricas e índice calculados
    processados = [
        r for r in todos
        if r.get("cortes_por_min") is not None and r.get("indice") is not None
    ]

    if not processados:
        print("Aviso: Nenhum dado processado com índice encontrado no banco.")
        print("Execute primeiro: python main.py processar && python main.py indice")
        return False

    grupos: Dict[str, List[Dict[str, Any]]] = {"alta": [], "baixa": []}
    for r in processados:
        grp = str(r["grupo"]).strip().lower()
        if grp in grupos:
            grupos[grp].append(r)
        else:
            grupos.setdefault(grp, []).append(r)

    campos_metricas = [
        ("cortes_por_min", "Cortes por minuto"),
        ("saturacao_media", "Saturação média (%)"),
        ("movimento_medio", "Movimento médio (Farneback)"),
        ("indice", "Índice de Estimulação (0 a 1)"),
        ("tempo_processamento_s", "Tempo de Processamento (s)"),
    ]

    linhas_csv = []
    print("\n" + "=" * 80)
    print("TABELA COMPARATIVA DE ESTATÍSTICAS DESCRITIVAS POR GRUPO")
    print("=" * 80)
    print(f"{'Grupo':<10} | {'Métrica':<32} | {'N':<4} | {'Média':<8} | {'Desvio':<8} | {'Mediana':<8}")
    print("-" * 80)

    estatisticas_gerais = {}

    for nome_grupo, lista in grupos.items():
        estatisticas_gerais[nome_grupo] = {}
        if not lista:
            print(f"{nome_grupo:<10} | (Nenhum vídeo registrado neste grupo)")
            continue

        for campo, rotulo in campos_metricas:
            vals = [float(item[campo]) for item in lista if item.get(campo) is not None]
            est = calcular_estatisticas_grupo(vals)
            estatisticas_gerais[nome_grupo][campo] = est

            print(
                f"{nome_grupo:<10} | {rotulo:<32} | {est['n']:<4} | "
                f"{est['media']:<8.2f} | {est['desvio_padrao']:<8.2f} | {est['mediana']:<8.2f}"
            )

            linhas_csv.append({
                "grupo": nome_grupo,
                "campo": campo,
                "metrica": rotulo,
                "n": est["n"],
                "media": est["media"],
                "desvio_padrao": est["desvio_padrao"],
                "mediana": est["mediana"],
            })
    print("=" * 80 + "\n")

    # 1. Gravar CSV com o resumo estatístico
    caminho_csv_resumo = diretorio_saida / "comparacao_estatisticas.csv"
    with open(caminho_csv_resumo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["grupo", "campo", "metrica", "n", "media", "desvio_padrao", "mediana"]
        )
        writer.writeheader()
        writer.writerows(linhas_csv)
    print(f"Resumo estatístico salvo em: {caminho_csv_resumo}")

    # 2. Gravar CSV completo com todos os vídeos individuais
    caminho_csv_completo = diretorio_saida / "dados_completos_videos.csv"
    with open(caminho_csv_completo, "w", newline="", encoding="utf-8") as f:
        colunas = [
            "video_id", "arquivo", "grupo", "fonte", "link", "duracao_s",
            "cortes_por_min", "saturacao_media", "movimento_medio",
            "indice", "tempo_processamento_s"
        ]
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(processados)
    print(f"Dados individuais salvos em: {caminho_csv_completo}")

    # 3. Gerar Gráficos Comparativos com Matplotlib
    gerar_graficos(estatisticas_gerais, diretorio_saida)
    return True


def gerar_graficos(estatisticas: Dict[str, Dict[str, Dict[str, float]]], diretorio_saida: Path) -> None:
    """
    Gera dois gráficos explicativos em formato PNG:
    1. Comparação direta da média do Índice de Estimulação Visual.
    2. Comparação das três métricas individuais entre os grupos.
    """
    grupos_disponiveis = [g for g in ["alta", "baixa"] if g in estatisticas and estatisticas[g]]
    if len(grupos_disponiveis) < 2:
        # Se houver outros nomes de grupo além de alta/baixa, usar as chaves existentes
        grupos_disponiveis = [g for g in estatisticas.keys() if estatisticas[g]]

    if not grupos_disponiveis:
        return

    # Cores acadêmicas e neutras (sem juízo de valor, apenas diferenciação visual)
    cores = {"alta": "#E63946", "baixa": "#457B9D"}

    # --------------------------------------------------------------------------
    # Gráfico 1: Média do Índice de Estimulação Visual
    # --------------------------------------------------------------------------
    plt.figure(figsize=(7, 5))
    x = np.arange(len(grupos_disponiveis))
    medias_indice = [estatisticas[g]["indice"]["media"] for g in grupos_disponiveis]
    desvios_indice = [estatisticas[g]["indice"]["desvio_padrao"] for g in grupos_disponiveis]
    cores_barras = [cores.get(g, "#6c757d") for g in grupos_disponiveis]

    barras = plt.bar(
        x, medias_indice, yerr=desvios_indice, capsize=6,
        color=cores_barras, alpha=0.88, width=0.5, edgecolor="black"
    )

    # Anotações dos valores médios acima das barras
    for bar in barras:
        altura = bar.get_height()
        plt.annotate(
            f"{altura:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, altura),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )

    rotulos_grupos = [f"Grupo {g.capitalize()} (n={estatisticas[g]['indice']['n']})" for g in grupos_disponiveis]
    plt.xticks(x, rotulos_grupos, fontsize=11)
    plt.ylabel("Índice de Estimulação Visual (0 a 1)", fontsize=11)
    plt.ylim(0, 1.15)
    plt.title("Comparação do Índice de Estimulação Visual entre Grupos", fontsize=13, pad=15)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    caminho_grafico1 = diretorio_saida / "grafico_indice_comparativo.png"
    plt.savefig(caminho_grafico1, dpi=300)
    plt.close()
    print(f"Gráfico do índice salvo em: {caminho_grafico1}")

    # --------------------------------------------------------------------------
    # Gráfico 2: Comparação das 3 Métricas Individuais
    # --------------------------------------------------------------------------
    metricas_chave = [
        ("cortes_por_min", "Cortes / min"),
        ("saturacao_media", "Saturação (%)"),
        ("movimento_medio", "Movimento médio"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, (chave, titulo_metrica) in zip(axes, metricas_chave):
        vals_media = [estatisticas[g][chave]["media"] for g in grupos_disponiveis]
        vals_desvio = [estatisticas[g][chave]["desvio_padrao"] for g in grupos_disponiveis]

        barras_sub = ax.bar(
            x, vals_media, yerr=vals_desvio, capsize=5,
            color=cores_barras, alpha=0.85, width=0.5, edgecolor="black"
        )
        for b in barras_sub:
            h = b.get_height()
            ax.annotate(
                f"{h:.1f}",
                xy=(b.get_x() + b.get_width() / 2, h),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center", va="bottom", fontsize=10, fontweight="bold"
            )

        ax.set_xticks(x)
        ax.set_xticklabels([g.capitalize() for g in grupos_disponiveis], fontsize=10)
        ax.set_title(titulo_metrica, fontsize=12)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.suptitle("Comparação Detalhada das Três Métricas por Grupo", fontsize=14, y=1.02)
    plt.tight_layout()

    caminho_grafico2 = diretorio_saida / "grafico_metricas_comparativo.png"
    plt.savefig(caminho_grafico2, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Gráfico das métricas salvo em: {caminho_grafico2}")
