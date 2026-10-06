"""
Módulo de Métricas de Processamento de Imagens (metricas.py)
------------------------------------------------------------
Este módulo é responsável por extrair as três características visuais fundamentais:
1. Frequência de cortes por minuto (mudanças bruscas de cena).
2. Saturação média das cores (vivacidade/intensidade das cores).
3. Quantidade média de movimento (fluxo óptico denso).

Cada função foi projetada de forma modular, clara e com explicações conceituais
para facilitar a apresentação em banca acadêmica.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import cv2
import numpy as np

import config


def obter_informacoes_video(caminho_video: str) -> Tuple[cv2.VideoCapture, float, int, float]:
    """
    Abre o arquivo de vídeo e extrai metadados básicos:
    - fps: quadros por segundo
    - total_frames: contagem total de frames
    - duracao_s: duração estimada em segundos
    """
    caminho = Path(caminho_video)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {caminho_video}")

    cap = cv2.VideoCapture(str(caminho))
    if not cap.isOpened():
        raise ValueError(f"Não foi possível abrir o arquivo de vídeo: {caminho_video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Proteção para vídeos com FPS inválido ou não detectado
    if fps is None or fps <= 0:
        fps = 30.0

    duracao_s = total_frames / fps if total_frames > 0 else 0.0
    return cap, fps, total_frames, duracao_s


def redimensionar_frame(frame: np.ndarray, largura: int = config.LARGURA_REDUZIDA) -> np.ndarray:
    """
    Redimensiona o frame proporcionalmente para uma largura padrão (ex: 320px).
    Isso reduz drasticamente a carga computacional sem comprometer
    a fidelidade estatística das cores e dos movimentos globais.
    """
    h, w = frame.shape[:2]
    if w <= largura:
        return frame
    nova_altura = int(h * (largura / w))
    return cv2.resize(frame, (largura, nova_altura), interpolation=cv2.INTER_AREA)


# ==============================================================================
# MÉTRICA 1: DETECÇÃO DE CORTES DE CENA (MUDANÇAS BRUSCAS)
# ==============================================================================
def detectar_cortes(
    caminho_video: str,
    largura_reduzida: int = config.LARGURA_REDUZIDA,
    limiar_corte: float = config.LIMIAR_CORTE,
    intervalo_min_s: float = config.INTERVALO_MIN_CORTES_S,
) -> Tuple[int, List[float], float]:
    """
    Detecta cortes de cena comparando histogramas de cores no espaço HSV entre
    frames consecutivos.

    POR QUE HISTOGRAMAS?
    O histograma de cor é a contagem de quantos pixels existem de cada cor.
    Em quadros consecutivos da mesma cena, a distribuição de cores é muito parecida.
    Em um corte, a nova cena provoca uma mudança súbita nessa distribuição,
    gerando uma queda acentuada na correlação entre os histogramas consecutivos.

    Retorna:
    - total_cortes: número absoluto de cortes detectados.
    - instantes_cortes: lista com os segundos exatos em que cada corte ocorreu.
    - cortes_por_min: taxa normalizada de cortes por minuto de vídeo.
    """
    cap, fps, total_frames, duracao_s = obter_informacoes_video(caminho_video)

    hist_anterior = None
    instantes_cortes: List[float] = []
    ultimo_corte_tempo = -intervalo_min_s  # Permite corte logo no início se houver
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensionamento para ganho de desempenho
        frame_pequeno = redimensionar_frame(frame, largura_reduzida)

        # Conversão para HSV: separa matiz (H), saturação (S) e luminosidade (V)
        hsv = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2HSV)

        # O histograma de cor é a contagem de quantos pixels existem de cada cor.
        # Em quadros consecutivos da mesma cena, a distribuição de cores é muito parecida.
        # Em um corte, a nova cena provoca uma mudança súbita nessa distribuição.
        # Histograma 3D com 8 divisões em cada canal (8x8x8 = 512 faixas)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        if hist_anterior is not None:
            # Compara correlação entre o histograma anterior e o atual
            # Correlação varia de -1 (oposto) a 1 (idêntico)
            correlacao = cv2.compareHist(hist_anterior, hist, cv2.HISTCMP_CORREL)
            diferenca = 1.0 - correlacao

            tempo_atual_s = frame_idx / fps

            # Se a diferença ultrapassar o limiar e respeitar o intervalo mínimo:
            if diferenca > limiar_corte and (tempo_atual_s - ultimo_corte_tempo) >= intervalo_min_s:
                instantes_cortes.append(tempo_atual_s)
                ultimo_corte_tempo = tempo_atual_s

        hist_anterior = hist
        frame_idx += 1

    cap.release()

    total_cortes = len(instantes_cortes)
    # Cálculo de cortes por minuto: cortes / (duração em minutos)
    duracao_minutos = duracao_s / 60.0 if duracao_s > 0 else 1.0
    cortes_por_min = total_cortes / duracao_minutos if duracao_minutos > 0 else 0.0

    return total_cortes, instantes_cortes, cortes_por_min


# ==============================================================================
# MÉTRICA 2: SATURAÇÃO MÉDIA DAS CORES
# ==============================================================================
def calcular_saturacao_media(
    caminho_video: str,
    fps_amostragem: float = config.FPS_AMOSTRAGEM_COR,
) -> float:
    """
    Calcula a saturação média das cores do vídeo em uma escala de 0% a 100%.

    A saturação mede a 'pureza' ou vivacidade da cor. Vídeos de alta estimulação
    geralmente utilizam iluminação forte, cores vibrantes e contrastadas
    (alta saturação), enquanto vídeos sóbrios ou em escala de cinza possuem baixa saturação.

    O canal S (Saturation) do espaço HSV varia de 0 (cinza puro) a 255 (cor pura).
    Para otimizar o processamento, amostramos uma quantidade fixa de frames por segundo
    (ex: 2 fps).
    """
    cap, fps, total_frames, duracao_s = obter_informacoes_video(caminho_video)

    passo_frames = max(1, int(round(fps / fps_amostragem)))
    valores_saturacao: List[float] = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Processa apenas os frames selecionados pela taxa de amostragem
        if frame_idx % passo_frames == 0:
            frame_pequeno = redimensionar_frame(frame)
            hsv = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2HSV)
            # Canal S é o índice 1
            canal_s = hsv[:, :, 1]
            media_s_frame = float(np.mean(canal_s))
            # Converte de [0, 255] para porcentagem [0, 100]%
            saturacao_pct = (media_s_frame / 255.0) * 100.0
            valores_saturacao.append(saturacao_pct)

        frame_idx += 1

    cap.release()

    if not valores_saturacao:
        return 0.0

    return float(np.mean(valores_saturacao))


# ==============================================================================
# MÉTRICA 3: QUANTIDADE DE MOVIMENTO (FLUXO ÓPTICO DENSO DE FARNEBACK)
# ==============================================================================
def calcular_movimento_medio(
    caminho_video: str,
    instantes_cortes: List[float],
    largura_reduzida: int = config.LARGURA_REDUZIDA,
    fps_amostragem: float = config.FPS_AMOSTRAGEM_MOVIMENTO,
) -> float:
    """
    Calcula a quantidade média de movimento dos pixels entre frames consecutivos
    amostrados, utilizando o algoritmo de Fluxo Óptico Denso de Gunnar Farneback.

    O QUE É FLUXO ÓPTICO?
    É o padrão de movimento aparente dos pixels em uma sequência de imagens.
    Para cada pixel da imagem, o algoritmo estima um vetor (dx, dy) que indica
    para onde e com que intensidade aquele pixel se deslocou no quadro seguinte.
    A magnitude do vetor (|v| = sqrt(dx^2 + dy^2)) representa a velocidade daquele pixel.

    FILTRAGEM DE CORTES:
    Quando há um corte de cena, a imagem muda inteiramente. Se calculássemos o fluxo
    óptico entre o frame antes e depois do corte, obteríamos um falso pico de movimento
    gigantesco. Portanto, qualquer par de frames cujo intervalo contenha um corte
    detectado é DESCARTADO do cálculo.
    """
    cap, fps, total_frames, duracao_s = obter_informacoes_video(caminho_video)

    passo_frames = max(1, int(round(fps / fps_amostragem)))
    frame_idx = 0

    frame_cinza_anterior = None
    tempo_anterior_s = 0.0
    magnitudes_validas: List[float] = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % passo_frames == 0:
            tempo_atual_s = frame_idx / fps
            frame_pequeno = redimensionar_frame(frame, largura_reduzida)
            frame_cinza_atual = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2GRAY)

            if frame_cinza_anterior is not None:
                # Verifica se algum corte detectado ocorreu entre tempo_anterior e tempo_atual
                cruzou_corte = any(
                    tempo_anterior_s <= instante <= tempo_atual_s
                    for instante in instantes_cortes
                )

                if not cruzou_corte:
                    # Fluxo óptico de Farneback: rápido, denso e robusto para análise de vídeo
                    fluxo = cv2.calcOpticalFlowFarneback(
                        prev=frame_cinza_anterior,
                        next=frame_cinza_atual,
                        flow=None,
                        pyr_scale=0.5,
                        levels=3,
                        winsize=15,
                        iterations=3,
                        poly_n=5,
                        poly_sigma=1.2,
                        flags=0,
                    )
                    # Calcula a magnitude de cada vetor de deslocamento
                    magnitude, _ = cv2.cartToPolar(fluxo[..., 0], fluxo[..., 1])
                    # Magnitude média de movimento neste intervalo
                    magnitudes_validas.append(float(np.mean(magnitude)))

            frame_cinza_anterior = frame_cinza_atual
            tempo_anterior_s = tempo_atual_s

        frame_idx += 1

    cap.release()

    if not magnitudes_validas:
        return 0.0

    return float(np.mean(magnitudes_validas))


# ==============================================================================
# PROCESSAMENTO INTEGRADO DE UM VÍDEO
# ==============================================================================
def processar_video(caminho_video: str) -> Dict[str, Any]:
    """
    Executa a análise completa de um vídeo individualmente:
    1. Metadados e duração
    2. Cortes por minuto (e seus instantes)
    3. Saturação média das cores
    4. Movimento médio (descartando cortes)
    5. Medição de tempo de execução via time.perf_counter
    """
    inicio = time.perf_counter()

    cap, fps, total_frames, duracao_s = obter_informacoes_video(caminho_video)
    cap.release()

    # Passo 3: Cortes
    total_cortes, instantes_cortes, cortes_por_min = detectar_cortes(caminho_video)

    # Passo 4: Saturação
    saturacao_media = calcular_saturacao_media(caminho_video)

    # Passo 5: Movimento
    movimento_medio = calcular_movimento_medio(caminho_video, instantes_cortes)

    tempo_processamento_s = time.perf_counter() - inicio

    return {
        "arquivo": Path(caminho_video).name,
        "duracao_s": round(duracao_s, 2),
        "total_cortes": total_cortes,
        "instantes_cortes": instantes_cortes,
        "cortes_por_min": round(cortes_por_min, 2),
        "saturacao_media": round(saturacao_media, 2),
        "movimento_medio": round(movimento_medio, 3),
        "tempo_processamento_s": round(tempo_processamento_s, 2),
    }
