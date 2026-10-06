# AGENTS.md — Regras de Contexto do Projeto

## 1. Visão Geral do Projeto
- **Título**: Estimativa Computacional da Estimulação Visual em Vídeos Curtos por Processamento de Imagens
- **Disciplina**: Gestão de Projetos (Ciência da Computação — UNIP)
- **Objetivo**: Extrair métricas físicas de PDI (cortes, saturação HSV, fluxo óptico Farneback) de vídeos curtos (máx 60-100s) e comparar dois grupos: **Alta Estimulação** (15 vídeos) vs **Baixa Estimulação** (15 vídeos).

## 2. Stack Tecnológica
- **Linguagem**: Python 3.10+
- **Bibliotecas Permitidas**: `opencv-python`, `numpy`, `matplotlib` e biblioteca padrão (`sqlite3`, `argparse`, `csv`, `pathlib`, `unittest`).
- **Banco de Dados**: SQLite local (`estimulacao.db`).

## 3. Comandos do Pipeline
- **Passo 1 (Processar vídeos)**:
  `python main.py processar` (ou `python main.py processar --reprocessar`)
- **Passo 2 (Calcular índice 0 a 1)**:
  `python main.py indice`
- **Passo 3 (Gerar estatísticas e gráficos)**:
  `python main.py comparar`
- **Testes Unitários**:
  `python -m unittest discover -s testes -p "test_*.py" -v`

## 4. Estrutura e Convenções
- `config.py`: Parâmetros centrais de PDI (`LARGURA_REDUZIDA = 320`, `LIMIAR_CORTE = 0.5`, `FPS_AMOSTRAGEM_COR = 2`, `FPS_AMOSTRAGEM_MOVIMENTO = 5`).
- `metricas.py`: Funções puras e explicadas em português para banca acadêmica.
- `banco.py`: Persistência SQLite com constraints e chaves estrangeiras.
- `indice.py`: Normalização min-max e média simples (pesos iguais).
- `comparacao.py`: Estatísticas descritivas (média, desvio, mediana) e geração de gráficos via matplotlib.
- `videos.csv`: Metadados (`arquivo,grupo,fonte,link`), onde `grupo` deve ser estritamente `alta` ou `baixa`.
- `resultados/`: Onde são gravados os CSVs e gráficos gerados.

## 5. Limites e Restrições (Boundaries)
- **Não baixar vídeos automaticamente da internet**: Devem ser colocados localmente em `videos/`.
- **Análise estritamente de sinal visual (pixels)**: Sem IA generativa, sem redes neurais, sem análise de áudio ou semântica.
- **Transparência didática**: Funções curtas, nomes em português, código legível para apresentação em banca.
