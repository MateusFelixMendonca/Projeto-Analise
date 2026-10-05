"""
Módulo de Cálculo do Índice de Estimulação Visual (indice.py)
------------------------------------------------------------
Combina as três métricas computacionais (cortes/min, saturação média, movimento médio)
em um único indicador adimensional ponderado entre 0.0 e 1.0.

CONCEITO FUNDAMENTAL — ÍNDICE RELATIVO:
O índice é estritamente relativo ao conjunto amostral de vídeos analisados.
O valor 0.0 não significa ausência total de estímulo no universo, mas sim o vídeo
que apresentou a menor combinação de estímulos DENTRO DO CONJUNTO testado.
Analogamente, 1.0 é atribuído ao vídeo de maior estimulação combinada no conjunto.

MÉTODO DE NORMALIZAÇÃO:
Utiliza-se a normalização Min-Max para cada uma das 3 métricas:
    normalizado = (valor - minimo) / (maximo - minimo)
Se todos os vídeos tiverem o mesmo valor para uma métrica (máximo == mínimo),
o valor normalizado é definido como 0.0 para evitar divisão por zero.

CÁLCULO DO ÍNDICE:
    indice = (cpm_norm + sat_norm + mov_norm) / 3.0
"""

from typing import Any, Dict, List
import banco
import config


def normalizar_min_max(valores: List[float]) -> List[float]:
    """
    Aplica normalização min-max para transformar uma lista de números no intervalo [0, 1].
    Se o valor máximo for igual ao mínimo, retorna 0.0 para todos os itens,
    evitando divisão por zero.
    """
    if not valores:
        return []

    min_val = min(valores)
    max_val = max(valores)
    diferenca = max_val - min_val

    if diferenca == 0.0:
        return [0.0 for _ in valores]

    return [(v - min_val) / diferenca for v in valores]


def calcular_indices(registros: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Recebe a lista de registros de vídeos com suas métricas brutas
    (cortes_por_min, saturacao_media, movimento_medio) e calcula o índice final
    de estimulação visual (0 a 1) para cada um.
    """
    if not registros:
        return []

    # Extrai as séries individuais de cada métrica
    cpms = [float(r["cortes_por_min"]) for r in registros]
    sats = [float(r["saturacao_media"]) for r in registros]
    movs = [float(r["movimento_medio"]) for r in registros]

    # Normaliza cada dimensão de 0 a 1
    cpms_norm = normalizar_min_max(cpms)
    sats_norm = normalizar_min_max(sats)
    movs_norm = normalizar_min_max(movs)

    # Calcula a média simples das três métricas normalizadas
    resultados = []
    for i, r in enumerate(registros):
        idx = (cpms_norm[i] + sats_norm[i] + movs_norm[i]) / 3.0
        item = dict(r)
        item["cortes_por_min_norm"] = round(cpms_norm[i], 4)
        item["saturacao_media_norm"] = round(sats_norm[i], 4)
        item["movimento_medio_norm"] = round(movs_norm[i], 4)
        item["indice"] = round(idx, 4)
        resultados.append(item)

    return resultados


def recalcular_indices_banco(caminho_banco: str = config.CAMINHO_BANCO) -> int:
    """
    Lê todos os vídeos processados no banco de dados SQLite, calcula
    o índice de estimulação visual relativo de cada um e persiste
    o resultado na coluna 'indice'.
    Retorna o total de registros atualizados.
    """
    todos = banco.listar_todos_os_resultados(caminho_banco)
    processados = [r for r in todos if r.get("cortes_por_min") is not None]

    if not processados:
        print("Nenhum vídeo processado encontrado no banco de dados para cálculo do índice.")
        return 0

    com_indices = calcular_indices(processados)

    for item in com_indices:
        banco.atualizar_indice(
            video_id=item["video_id"],
            indice=item["indice"],
            caminho_banco=caminho_banco,
        )

    print(f"Índice de estimulação recalculado para {len(com_indices)} vídeos.")
    return len(com_indices)


if __name__ == "__main__":
    print("Demonstração manual do cálculo do índice de estimulação:")
    exemplo = [
        {"video_id": 1, "cortes_por_min": 0.0, "saturacao_media": 10.0, "movimento_medio": 0.5},
        {"video_id": 2, "cortes_por_min": 10.0, "saturacao_media": 50.0, "movimento_medio": 2.0},
        {"video_id": 3, "cortes_por_min": 20.0, "saturacao_media": 90.0, "movimento_medio": 3.5},
    ]
    res = calcular_indices(exemplo)
    for r in res:
        print(f"Vídeo {r['video_id']}: CPM_norm={r['cortes_por_min_norm']} Sat_norm={r['saturacao_media_norm']} Mov_norm={r['movimento_medio_norm']} -> ÍNDICE={r['indice']}")
