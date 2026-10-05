"""
Módulo de Configuração (config.py)
----------------------------------
Define todos os parâmetros ajustáveis e caminhos do projeto para
o processamento de imagens e estimativa de estimulação visual.
"""

from pathlib import Path

# ==============================================================================
# CAMINHOS E DIRETÓRIOS
# ==============================================================================

# Diretório onde os arquivos de vídeo (.mp4, etc.) devem ser colocados
DIRETORIO_VIDEOS = Path("videos")

# Diretório onde relatórios CSV e gráficos comparativos são gravados
DIRETORIO_RESULTADOS = Path("resultados")

# Nome do arquivo do banco de dados SQLite local
CAMINHO_BANCO = "estimulacao.db"

# Arquivo CSV que lista os vídeos com grupo (alta/baixa), fonte e link
ARQUIVO_CSV_VIDEOS = "videos.csv"


# ==============================================================================
# PARÂMETROS DE PROCESSAMENTO DE IMAGENS
# ==============================================================================

# Largura em pixels para redimensionar os frames durante a análise.
# Reduz o tempo de processamento e uso de memória mantendo a precisão das métricas.
LARGURA_REDUZIDA = 320

# Limiar de diferença de histograma (1 - correlação) para detectar cortes de cena.
# Quando a diferença entre dois frames consecutivos supera este valor,
# considera-se que houve mudança brusca de cena.
LIMIAR_CORTE = 0.5

# Intervalo mínimo (em segundos) entre cortes consecutivos detectados.
# Ignora mudanças muito próximas causadas por compressão ou ruído no vídeo.
INTERVALO_MIN_CORTES_S = 0.3

# Taxa de amostragem (frames por segundo) para medir a saturação média das cores.
# 2 frames por segundo é suficiente para caracterizar a vivacidade das cores.
FPS_AMOSTRAGEM_COR = 2

# Taxa de amostragem (frames por segundo) para calcular o movimento por fluxo óptico.
# 5 frames por segundo permite capturar movimentos humanos e de câmera eficientemente.
FPS_AMOSTRAGEM_MOVIMENTO = 5
