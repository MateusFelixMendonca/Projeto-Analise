# GEMINI.md — Passo a passo para gerar o código do protótipo

## 1. Contexto do projeto

Projeto acadêmico (disciplina de Gestão de Projetos, Ciência da Computação, UNIP).
Título: **Estimativa computacional da estimulação visual em vídeos curtos por Processamento de Imagens**.

O protótipo é um programa em **Python** que analisa vídeos curtos e calcula três métricas de Processamento de Imagens:

1. **Frequência de cortes por minuto** (mudanças bruscas de cena).
2. **Saturação média das cores**.
3. **Quantidade de movimento** (fluxo óptico).

As métricas são gravadas em um banco **SQLite**, combinadas em um **índice de estimulação visual (0 a 1)** e usadas para comparar dois grupos de vídeos: **15 de alta estimulação** (TikTok, Reels, Shorts) e **15 de baixa estimulação** (palestras, entrevistas, documentários). Cada vídeo tem no máximo 60 segundos.

## 2. Regras gerais (obrigatórias)

- Linguagem: Python 3. Bibliotecas permitidas: `opencv-python`, `numpy`, `matplotlib` e a biblioteca padrão (`sqlite3`, `argparse`, `csv`, `time`, `pathlib`). `scipy` só se for explicitamente pedido.
- **Código simples e legível.** Os três integrantes do grupo precisam entender e explicar cada trecho em uma banca. Funções curtas, nomes claros e **comentários em português** explicando o que cada bloco faz e por quê.
- **Sem interface gráfica.** Apenas linha de comando.
- **Não baixar vídeos da internet.** Os vídeos são colocados manualmente pelo grupo na pasta `videos/`.
- **Não analisar o conteúdo ou o assunto dos vídeos**, apenas pixels (cor, cortes, movimento).
- **Não adicionar funcionalidades fora do escopo** (nada de bloqueio de vídeo, aprendizado de máquina, análise de áudio, redes neurais).
- Todos os parâmetros ajustáveis (limiares, taxa de amostragem) ficam em um único arquivo `config.py`, com comentários.
- Ao fim de cada etapa, **pare, mostre o que foi feito e aguarde confirmação** antes de seguir.

## 3. Estrutura de pastas esperada

```
projeto/
├── GEMINI.md
├── README.md
├── requirements.txt
├── config.py
├── main.py              # linha de comando
├── metricas.py          # cortes, saturação e movimento
├── banco.py             # SQLite
├── indice.py            # normalização e cálculo do índice
├── comparacao.py        # tabela e gráfico por grupo
├── testes/
│   └── test_metricas.py
├── videos/              # vídeos colocados manualmente
├── videos.csv           # lista e classificação dos vídeos
└── resultados/          # CSV e gráficos gerados
```

## 4. Passos

### Passo 1 — Ambiente e esqueleto

- Criar a estrutura de pastas acima.
- Criar `requirements.txt` com `opencv-python`, `numpy` e `matplotlib`.
- Criar `config.py` com os parâmetros (valores iniciais sugeridos):
  - `LARGURA_REDUZIDA = 320` (redimensionar frames para acelerar o processamento)
  - `LIMIAR_CORTE = 0.5` (ver Passo 3)
  - `INTERVALO_MIN_CORTES_S = 0.3` (ignora cortes muito próximos)
  - `FPS_AMOSTRAGEM_COR = 2` (frames por segundo analisados na saturação)
  - `FPS_AMOSTRAGEM_MOVIMENTO = 5` (frames por segundo analisados no fluxo óptico)
- Criar `videos.csv` de exemplo com as colunas: `arquivo,grupo,fonte,link` (grupo é `alta` ou `baixa`).
- **Verificação:** `python -c "import cv2; print(cv2.__version__)"` funciona.

### Passo 2 — Banco de dados SQLite (`banco.py`)

Criar o arquivo `estimulacao.db` com duas tabelas:

- `videos(id INTEGER PRIMARY KEY, arquivo TEXT UNIQUE, grupo TEXT, fonte TEXT, link TEXT, duracao_s REAL)`
- `metricas(id INTEGER PRIMARY KEY, video_id INTEGER, cortes_por_min REAL, saturacao_media REAL, movimento_medio REAL, indice REAL, tempo_processamento_s REAL, FOREIGN KEY(video_id) REFERENCES videos(id))`

Funções: criar tabelas, inserir vídeo, inserir/atualizar métricas, listar todos os resultados.
- **Verificação:** rodar a criação duas vezes não gera erro nem duplica dados.

### Passo 3 — Detecção de cortes (`metricas.py`)

- Ler o vídeo com `cv2.VideoCapture`; obter FPS, total de frames e duração.
- Para cada par de frames consecutivos, redimensionar, converter para **HSV** e calcular o histograma (por exemplo, 8x8x8 bins, normalizado).
- Comparar os histogramas com `cv2.compareHist` (método de correlação). Quando a **diferença** (1 − correlação) passar de `LIMIAR_CORTE`, contar um corte, respeitando `INTERVALO_MIN_CORTES_S`.
- Retornar o número de cortes, **os instantes dos cortes** (serão usados no Passo 5) e `cortes_por_min = cortes / (duracao_s / 60)`.
- Comentar no código por que o histograma é usado (mudança de cena altera a distribuição de cores de forma brusca).
- **Verificação:** ver Passo 8 (teste com vídeo sintético).

### Passo 4 — Saturação média

- Amostrar frames conforme `FPS_AMOSTRAGEM_COR`, converter para HSV e tirar a média do canal S.
- Retornar a média final em porcentagem (0 a 100), dividindo por 255.
- **Verificação:** um vídeo em preto e branco deve dar saturação próxima de 0.

### Passo 5 — Movimento por fluxo óptico

- Amostrar frames conforme `FPS_AMOSTRAGEM_MOVIMENTO`, em escala de cinza e reduzidos.
- Calcular o fluxo óptico denso com `cv2.calcOpticalFlowFarneback` entre frames amostrados consecutivos.
- Para cada par, calcular a **magnitude média** dos vetores (`cv2.cartToPolar`).
- **Descartar os pares que cruzam um corte** (usar os instantes do Passo 3), porque um corte gera um valor de movimento falso e enorme.
- Retornar a média das magnitudes dos pares restantes (`movimento_medio`).
- Comentar o que é fluxo óptico em linguagem simples.
- **Verificação:** um vídeo parado deve dar movimento próximo de 0.

### Passo 6 — Processamento dos vídeos (`main.py`)

Comando: `python main.py processar`

- Ler `videos.csv`, e para cada vídeo existente em `videos/`: calcular as três métricas, **medir o tempo de processamento** (`time.perf_counter`) e gravar no banco.
- Pular vídeos já processados e avisar sobre arquivos que não existem ou não abrem, sem travar o programa.
- Mostrar uma linha de progresso por vídeo.
- **Verificação:** processar 2 ou 3 vídeos de teste e conferir os dados no banco.

### Passo 7 — Índice de estimulação (`indice.py`)

Comando: `python main.py indice`

- Ler as métricas de **todos** os vídeos do banco.
- Normalizar cada métrica de 0 a 1 (min-max): `(valor − mínimo) / (máximo − mínimo)`. Se máximo e mínimo forem iguais, usar 0 para evitar divisão por zero.
- O índice é a **média simples** das três métricas normalizadas (pesos iguais).
- Atualizar a coluna `indice` no banco.
- Comentar que o índice é **relativo ao conjunto de vídeos analisados**: 0 é o menos estimulante do conjunto e 1 é o mais.
- **Verificação:** com valores conhecidos de exemplo, conferir o resultado à mão.

### Passo 8 — Testes (`testes/test_metricas.py`)

- Gerar com OpenCV **vídeos sintéticos** pequenos: (a) quadros que alternam bruscamente entre 3 cores diferentes (cortes conhecidos), (b) vídeo cinza parado, (c) vídeo colorido com um quadrado se movendo.
- Testar: o detector encontra aproximadamente o número de cortes esperado; o vídeo cinza tem saturação ≈ 0 e movimento ≈ 0; o vídeo com quadrado em movimento tem movimento > 0.
- Testar a normalização com três valores de exemplo.
- **Verificação:** todos os testes passam com `python -m unittest`.

### Passo 9 — Comparação entre grupos (`comparacao.py`)

Comando: `python main.py comparar`

- Calcular, por grupo (`alta` e `baixa`): média, desvio padrão e mediana do índice e de cada métrica, além do tempo médio de processamento.
- Salvar uma **tabela CSV** em `resultados/` e imprimir a tabela no terminal.
- Gerar um **gráfico de barras** (matplotlib) comparando a média do índice entre os grupos, e outro com as três métricas por grupo, salvos como PNG em `resultados/`.
- Não afirmar causa nem julgamento ("nocivo"); mostrar apenas os números.
- **Verificação:** os arquivos são gerados e o gráfico abre corretamente.

### Passo 10 — Documentação

- Escrever `README.md` curto, em português: o que o programa faz, como instalar, como colocar os vídeos, como preencher `videos.csv` e a ordem dos comandos (`processar`, `indice`, `comparar`).
- Incluir uma seção "Como o índice é calculado" com a fórmula e um exemplo numérico.
- Incluir uma seção "Limitações": índice relativo ao conjunto, amostra de 30 vídeos, análise apenas visual.

## 5. Critérios de pronto

- Os três comandos rodam em sequência sem erro em um computador comum.
- Os 30 vídeos são processados e gravados no banco.
- O índice e a comparação entre os grupos são gerados em `resultados/`.
- Os testes passam.
- Qualquer integrante do grupo consegue explicar cada arquivo.
