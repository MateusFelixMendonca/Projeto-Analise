"""
Testes Unitários Automatizados (testes/test_metricas.py)
--------------------------------------------------------
Valida os cálculos de métricas com vídeos sintéticos gerados dinamicamente:
1. Detecção de cortes conhecidos (transição brusca de cores).
2. Saturação nula e movimento nulo em vídeo cinza estático.
3. Movimento detectável em vídeo com objeto em deslocamento.
4. Normalização min-max das métricas.
"""

import os
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np

from metricas import (
    calcular_movimento_medio,
    calcular_saturacao_media,
    detectar_cortes,
    processar_video,
)
from indice import normalizar_min_max, calcular_indices


class TestMetricasSinteticas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Cria arquivos de vídeo temporários com características sintéticas conhecidas.
        """
        cls.diretorio_temp = tempfile.TemporaryDirectory()
        cls.dir_path = Path(cls.diretorio_temp.name)

        largura, altura = 160, 120
        fps = 30.0
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        # --- 1. Vídeo com 2 cortes bem definidos (3 cores diferentes, 1 segundo cada) ---
        cls.caminho_cortes = str(cls.dir_path / "teste_cortes.mp4")
        writer_cortes = cv2.VideoWriter(cls.caminho_cortes, fourcc, fps, (largura, altura))
        # 30 frames Vermelho (BGR: 0, 0, 255)
        for _ in range(30):
            frame = np.full((altura, largura, 3), (0, 0, 255), dtype=np.uint8)
            writer_cortes.write(frame)
        # 30 frames Verde (BGR: 0, 255, 0) -> CORTE 1
        for _ in range(30):
            frame = np.full((altura, largura, 3), (0, 255, 0), dtype=np.uint8)
            writer_cortes.write(frame)
        # 30 frames Azul (BGR: 255, 0, 0) -> CORTE 2
        for _ in range(30):
            frame = np.full((altura, largura, 3), (255, 0, 0), dtype=np.uint8)
            writer_cortes.write(frame)
        writer_cortes.release()

        # --- 2. Vídeo Cinza Parado (sem cortes, saturação = 0, movimento = 0) ---
        cls.caminho_cinza = str(cls.dir_path / "teste_cinza_parado.mp4")
        writer_cinza = cv2.VideoWriter(cls.caminho_cinza, fourcc, fps, (largura, altura))
        frame_cinza = np.full((altura, largura, 3), (128, 128, 128), dtype=np.uint8)
        for _ in range(60):  # 2 segundos
            writer_cinza.write(frame_cinza)
        writer_cinza.release()

        # --- 3. Vídeo com Movimento Contínuo (quadrado colorido se deslocando) ---
        cls.caminho_movimento = str(cls.dir_path / "teste_movimento.mp4")
        writer_mov = cv2.VideoWriter(cls.caminho_movimento, fourcc, fps, (largura, altura))
        for i in range(60):  # 2 segundos
            frame = np.zeros((altura, largura, 3), dtype=np.uint8)
            x_pos = (i * 2) % (largura - 30)
            cv2.rectangle(frame, (x_pos, 40), (x_pos + 25, 75), (0, 255, 255), -1)
            writer_mov.write(frame)
        writer_mov.release()

    @classmethod
    def tearDownClass(cls):
        cls.diretorio_temp.cleanup()

    def test_deteccao_cortes(self):
        """
        Verifica se o detector identifica aproximadamente os 2 cortes reais inseridos.
        """
        total_cortes, instantes, cpm = detectar_cortes(self.caminho_cortes)
        self.assertEqual(total_cortes, 2, f"Esperado 2 cortes, mas obteve {total_cortes}")
        self.assertEqual(len(instantes), 2)
        # Instante 1 deve ser por volta de 1.0s e Instante 2 por volta de 2.0s
        self.assertAlmostEqual(instantes[0], 1.0, delta=0.2)
        self.assertAlmostEqual(instantes[1], 2.0, delta=0.2)
        # 2 cortes em 3 segundos = 2 / (3/60) = 40 cortes por minuto
        self.assertAlmostEqual(cpm, 40.0, delta=2.0)

    def test_video_cinza_saturacao_e_movimento_nulos(self):
        """
        Em vídeo cinza sem movimento, saturação deve ser 0% e movimento deve ser ~0.
        """
        sat = calcular_saturacao_media(self.caminho_cinza)
        self.assertAlmostEqual(sat, 0.0, delta=3.0, msg=f"Saturação esperada próxima de 0%, obteve {sat}%")

        mov = calcular_movimento_medio(self.caminho_cinza, instantes_cortes=[])
        self.assertAlmostEqual(mov, 0.0, delta=0.05, msg=f"Movimento esperado ~0, obteve {mov}")

    def test_video_com_movimento(self):
        """
        Vídeo com retângulo em movimento deve apresentar movimento médio estritamente positivo.
        """
        mov = calcular_movimento_medio(self.caminho_movimento, instantes_cortes=[])
        self.assertGreater(mov, 0.1, f"Movimento deveria ser significante, obteve {mov}")

        sat = calcular_saturacao_media(self.caminho_movimento)
        self.assertGreater(sat, 1.0, f"Saturação deveria ser positiva, obteve {sat}%")

    def test_processar_video_completo(self):
        """
        Verifica a execução integrada do processamento retornando todas as chaves esperadas.
        """
        resultado = processar_video(self.caminho_cortes)
        self.assertIn("duracao_s", resultado)
        self.assertIn("cortes_por_min", resultado)
        self.assertIn("saturacao_media", resultado)
        self.assertIn("movimento_medio", resultado)
        self.assertIn("tempo_processamento_s", resultado)
    def test_normalizacao_min_max(self):
        """
        Valida normalização min-max padrão e caso de valores constantes.
        """
        valores = [10.0, 20.0, 30.0]
        norm = normalizar_min_max(valores)
        self.assertEqual(norm, [0.0, 0.5, 1.0])

        constantes = [5.0, 5.0, 5.0]
        norm_const = normalizar_min_max(constantes)
        self.assertEqual(norm_const, [0.0, 0.0, 0.0])

    def test_calculo_indices(self):
        """
        Valida o cálculo do índice de estimulação para 3 vídeos com valores conhecidos.
        Vídeo 1 tem os menores valores em tudo -> índice deve ser 0.0.
        Vídeo 2 tem valores intermediários exatos (0.5 em tudo) -> índice deve ser 0.5.
        Vídeo 3 tem os maiores valores em tudo -> índice deve ser 1.0.
        """
        exemplo = [
            {"video_id": 1, "cortes_por_min": 0.0, "saturacao_media": 10.0, "movimento_medio": 0.5},
            {"video_id": 2, "cortes_por_min": 10.0, "saturacao_media": 50.0, "movimento_medio": 2.0},
            {"video_id": 3, "cortes_por_min": 20.0, "saturacao_media": 90.0, "movimento_medio": 3.5},
        ]
        res = calcular_indices(exemplo)
        self.assertAlmostEqual(res[0]["indice"], 0.0, places=4)
        self.assertAlmostEqual(res[1]["indice"], 0.5, places=4)
        self.assertAlmostEqual(res[2]["indice"], 1.0, places=4)


if __name__ == "__main__":
    unittest.main()

