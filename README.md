# Estimativa Computacional da Estimulação Visual em Vídeos Curtos por Processamento de Imagens

Projeto acadêmico desenvolvido para a disciplina de **Gestão de Projetos** (Ciência da Computação — UNIP).

---

## 1. O que o programa faz

Este protótipo analisa arquivos de vídeos curtos (máximo de 60 segundos) e extrai computacionalmente três métricas quantitativas de Processamento Digital de Imagens (PDI):

1. **Frequência de cortes por minuto:** Detecta mudanças bruscas de tomada/cena comparando histogramas de cores 3D no espaço de cores HSV entre quadros consecutivos.
2. **Saturação média das cores (%):** Mede a vivacidade e intensidade cromática através da média amostrada do canal $S$ do espaço HSV.
3. **Quantidade de movimento médio:** Estima o deslocamento físico dos pixels através do algoritmo de **Fluxo Óptico Denso de Gunnar Farneback**, descartando automaticamente intervalos onde ocorreram cortes (para evitar picos falsos de movimento).

Os dados são armazenados localmente em um banco de dados SQLite (`estimulacao.db`), normalizados e combinados em um **Índice de Estimulação Visual (0 a 1)** para fins comparativos entre dois grupos:
- **Grupo Alta Estimulação:** Vídeos dinâmicos típicos de redes sociais rápidas (TikTok, Instagram Reels, YouTube Shorts).
- **Grupo Baixa Estimulação:** Vídeos sóbrios com tomadas longas e pouca variação visual (palestras, entrevistas, documentários).

---

## 2. Requisitos e Instalação

O projeto requer **Python 3.10+**. As dependências necessárias são restritas às permitidas pela especificação: `opencv-python`, `numpy` e `matplotlib`.

### Passo a passo para instalar:

1. Clone ou baixe este repositório.
2. (Opcional, mas recomendado) Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   # No Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # No Linux/Mac:
   source .venv/bin/activate
   ```
3. Instale as bibliotecas:
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Como organizar e preparar os vídeos

1. Coloque seus arquivos de vídeo (formatos `.mp4`, `.mkv`, etc.) na pasta `videos/`.
2. Abra o arquivo `videos.csv` na raiz do projeto e cadastre cada vídeo com suas informações:
   ```csv
   arquivo,grupo,fonte,link
   meu_video_tiktok1.mp4,alta,TikTok,https://www.tiktok.com/@canal/video/123
   minha_palestra1.mp4,baixa,YouTube,https://www.youtube.com/watch?v=abc
   ```
   - **`arquivo`**: Nome exato do arquivo contido dentro da pasta `videos/`.
   - **`grupo`**: Classificação como `alta` ou `baixa`.
   - **`fonte`**: Plataforma ou origem do vídeo (ex: TikTok, Reels, TED, TV Cultura).
   - **`link`**: URL de referência do vídeo original.

---

## 4. Ordem de Execução dos Comandos

O protótipo funciona via linha de comando em três passos sequenciais:

### Passo A — Processar os vídeos
Extrai as métricas de cada vídeo da pasta `videos/` e grava no banco SQLite:
```bash
python main.py processar
```
*Observações:*
- O programa exibe uma linha de progresso para cada arquivo com duração e tempo de análise.
- Vídeos já processados são ignorados automaticamente para não recomputar dados desnecessariamente. Para forçar novo processamento, use a opção `--reprocessar`.
- Se um vídeo do CSV não for encontrado no disco, o programa emite um aviso e continua os demais sem travar.

### Passo B — Calcular o Índice de Estimulação
Normaliza as três métricas computadas e calcula o índice de 0 a 1 (média simples com pesos iguais):
```bash
python main.py indice
```

### Passo C — Gerar Comparação Estatística e Gráficos
Calcula média, desvio padrão e mediana por grupo, gerando tabelas e figuras:
```bash
python main.py comparar
```

Arquivos gerados na pasta `resultados/`:
- `comparacao_estatisticas.csv`: Tabela com N, média, desvio padrão e mediana de cada métrica por grupo.
- `dados_completos_videos.csv`: Tabela com todas as métricas detalhadas de cada vídeo individualmente.
- `grafico_indice_comparativo.png`: Gráfico de barras com a média e desvio padrão do índice de estimulação entre os grupos.
- `grafico_metricas_comparativo.png`: Comparação lado a lado das 3 métricas individuais (cortes, saturação e movimento).

---

## 5. Como o Índice de Estimulação é Calculado

O índice é obtido através de uma **média simples (pesos iguais)** das três métricas após passarem por uma **normalização Min-Max**:

$$\text{Normalizado} = \frac{\text{valor} - \text{mínimo}}{\text{máximo} - \text{mínimo}}$$

$$\text{Índice} = \frac{\text{Cortes}_{\text{norm}} + \text{Saturação}_{\text{norm}} + \text{Movimento}_{\text{norm}}}{3}$$

### Exemplo Numérico Manual:

Suponha um conjunto de 3 vídeos analisados:

| Vídeo | Cortes / min | Saturação (%) | Movimento |
| :--- | :--- | :--- | :--- |
| **Vídeo A** (mínimos) | 0.0 | 10.0% | 0.50 |
| **Vídeo B** (médios) | 10.0 | 50.0% | 2.00 |
| **Vídeo C** (máximos) | 20.0 | 90.0% | 3.50 |

1. **Faixas de variação:**
   - Cortes: mín = 0, máx = 20 (delta = 20)
   - Saturação: mín = 10, máx = 90 (delta = 80)
   - Movimento: mín = 0.5, máx = 3.5 (delta = 3.0)

2. **Cálculo para o Vídeo B:**
   - $\text{Cortes}_{\text{norm}} = (10 - 0) / 20 = 0.50$
   - $\text{Saturação}_{\text{norm}} = (50 - 10) / 80 = 0.50$
   - $\text{Movimento}_{\text{norm}} = (2.0 - 0.5) / 3.0 = 0.50$
   - $\text{Índice do Vídeo B} = (0.50 + 0.50 + 0.50) / 3 = \mathbf{0.50}$

O Vídeo A (menores valores em tudo) recebe índice **0.00**, e o Vídeo C (maiores valores) recebe índice **1.00**.

---

## 6. Resultados Obtidos na Análise (30 Vídeos)

Amostra analisada com $N = 15$ vídeos no grupo **Alta Estimulação** e $N = 15$ vídeos no grupo **Baixa Estimulação**:

| Grupo | Métrica | N | Média | Desvio Padrão | Mediana |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Alta** | **Cortes por minuto** | 15 | **1,81** | 2,61 | 0,00 |
| **Alta** | **Saturação média (%)** | 15 | **39,45%** | 10,94% | 37,28% |
| **Alta** | **Movimento médio (Farneback)** | 15 | **3,92** | 3,74 | 2,04 |
| **Alta** | **Índice de Estimulação (0 a 1)** | 15 | **0,24** | 0,15 | 0,17 |
| **Alta** | *Tempo de Processamento (s)* | 15 | 67,27s | 61,79s | 85,09s |
| **Baixa** | **Cortes por minuto** | 15 | **20,81** | 23,10 | 18,42 |
| **Baixa** | **Saturação média (%)** | 15 | **37,36%** | 12,77% | 34,90% |
| **Baixa** | **Movimento médio (Farneback)** | 15 | **4,05** | 3,16 | 4,30 |
| **Baixa** | **Índice de Estimulação (0 a 1)** | 15 | **0,30** | 0,18 | 0,29 |
| **Baixa** | *Tempo de Processamento (s)* | 15 | 46,83s | 45,89s | 22,96s |

Os gráficos comparativos estão disponíveis em:
- `resultados/grafico_indice_comparativo.png`
- `resultados/grafico_metricas_comparativo.png`

---

## 7. Limitações do Estudo

1. **Índice Relativo:** O índice calculado é estritamente **relativo à amostra de vídeos analisada no lote**. Um valor 0.0 não significa ausência absoluta de estímulo em termos universais, mas sim o vídeo com menor estimulação dentro daquele conjunto específico.
2. **Amostra Reduzida:** O escopo do protótipo foi desenhado para testar e comparar 30 vídeos (15 de alta estimulação e 15 de baixa), servindo como prova de conceito acadêmica.
3. **Análise Puramente Visual (PDI):** O protótipo foca exclusivamente em características físicas de sinal de vídeo (pixels, luminosidade, cor e deslocamento). Não realiza transcrição de áudio, detecção de rostos, classificação semântica nem julgamento de conteúdo.

---

## 8. Como Executar os Testes Automatizados

O projeto inclui uma suíte de testes unitários que cria vídeos sintéticos dinamicamente na memória/disco temporário para testar cada métrica sem depender de arquivos externos:

```bash
python -m unittest discover -s testes -p "test_*.py" -v
```

Todos os testes validam matematicamente a detecção de cortes, saturação nula em tons de cinza, fluxo óptico em objetos móveis e a normalização do índice.
