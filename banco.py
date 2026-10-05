"""
Módulo de Banco de Dados (banco.py)
-----------------------------------
Gerencia o banco SQLite (estimulacao.db) para persistência das informações
dos vídeos analisados e das métricas computadas.
"""

import sqlite3
from typing import Any, Dict, List, Optional
import config


def conectar(caminho_banco: str = config.CAMINHO_BANCO) -> sqlite3.Connection:
    """
    Estabelece conexão com o banco SQLite e ativa restrições de chave estrangeira.
    """
    conn = sqlite3.connect(caminho_banco)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas(caminho_banco: str = config.CAMINHO_BANCO) -> None:
    """
    Cria as tabelas 'videos' e 'metricas' se não existirem.
    Execuções repetidas não geram erro nem alteram dados existentes.
    """
    with conectar(caminho_banco) as conn:
        cursor = conn.cursor()

        # Tabela de metadados dos vídeos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo TEXT UNIQUE NOT NULL,
                grupo TEXT NOT NULL,
                fonte TEXT,
                link TEXT,
                duracao_s REAL
            );
        """)

        # Tabela de métricas extraídas por processamento de imagens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER UNIQUE NOT NULL,
                cortes_por_min REAL,
                saturacao_media REAL,
                movimento_medio REAL,
                indice REAL,
                tempo_processamento_s REAL,
                FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
            );
        """)
        conn.commit()


def inserir_ou_obter_video(
    arquivo: str,
    grupo: str,
    fonte: str = "",
    link: str = "",
    duracao_s: float = 0.0,
    caminho_banco: str = config.CAMINHO_BANCO,
) -> int:
    """
    Cadastra um vídeo na tabela 'videos' ou atualiza suas informações se já existir.
    Retorna o ID do vídeo no banco.
    """
    with conectar(caminho_banco) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO videos (arquivo, grupo, fonte, link, duracao_s)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(arquivo) DO UPDATE SET
                grupo = excluded.grupo,
                fonte = excluded.fonte,
                link = excluded.link,
                duracao_s = excluded.duracao_s;
        """, (arquivo, grupo, fonte, link, duracao_s))

        # Obter o id do vídeo registrado
        cursor.execute("SELECT id FROM videos WHERE arquivo = ?;", (arquivo,))
        row = cursor.fetchone()
        conn.commit()
        return int(row["id"])


def salvar_metricas(
    video_id: int,
    cortes_por_min: float,
    saturacao_media: float,
    movimento_medio: float,
    tempo_processamento_s: float,
    indice: Optional[float] = None,
    caminho_banco: str = config.CAMINHO_BANCO,
) -> None:
    """
    Insere ou substitui as métricas calculadas para determinado vídeo.
    """
    with conectar(caminho_banco) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metricas (
                video_id, cortes_por_min, saturacao_media,
                movimento_medio, indice, tempo_processamento_s
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                cortes_por_min = excluded.cortes_por_min,
                saturacao_media = excluded.saturacao_media,
                movimento_medio = excluded.movimento_medio,
                indice = excluded.indice,
                tempo_processamento_s = excluded.tempo_processamento_s;
        """, (
            video_id,
            cortes_por_min,
            saturacao_media,
            movimento_medio,
            indice,
            tempo_processamento_s,
        ))
        conn.commit()


def atualizar_indice(
    video_id: int,
    indice: float,
    caminho_banco: str = config.CAMINHO_BANCO,
) -> None:
    """
    Atualiza apenas o valor do índice de estimulação para um vídeo.
    """
    with conectar(caminho_banco) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE metricas
            SET indice = ?
            WHERE video_id = ?;
        """, (indice, video_id))
        conn.commit()


def obter_metricas_video(
    arquivo: str,
    caminho_banco: str = config.CAMINHO_BANCO,
) -> Optional[Dict[str, Any]]:
    """
    Retorna as métricas de um vídeo pelo nome do arquivo, ou None se ainda não processado.
    """
    with conectar(caminho_banco) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id AS video_id, v.arquivo, v.grupo, v.duracao_s,
                   m.cortes_por_min, m.saturacao_media, m.movimento_medio,
                   m.indice, m.tempo_processamento_s
            FROM videos v
            INNER JOIN metricas m ON v.id = m.video_id
            WHERE v.arquivo = ?;
        """, (arquivo,))
        row = cursor.fetchone()
        return dict(row) if row else None


def listar_todos_os_resultados(
    caminho_banco: str = config.CAMINHO_BANCO,
) -> List[Dict[str, Any]]:
    """
    Retorna todos os vídeos cadastrados juntamente com suas métricas (se houver).
    """
    with conectar(caminho_banco) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id AS video_id, v.arquivo, v.grupo, v.fonte, v.link, v.duracao_s,
                   m.cortes_por_min, m.saturacao_media, m.movimento_medio,
                   m.indice, m.tempo_processamento_s
            FROM videos v
            LEFT JOIN metricas m ON v.id = m.video_id
            ORDER BY v.id ASC;
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    print("Testando módulo de banco de dados...")
    # Verificação de idempotência (rodar duas vezes sem erro)
    criar_tabelas()
    criar_tabelas()
    print("Tabelas criadas com sucesso.")

    vid_id = inserir_ou_obter_video(
        arquivo="teste_exemplo.mp4",
        grupo="alta",
        fonte="TikTok",
        link="https://exemplo",
        duracao_s=15.5
    )
    salvar_metricas(
        video_id=vid_id,
        cortes_por_min=12.0,
        saturacao_media=65.4,
        movimento_medio=3.2,
        tempo_processamento_s=1.8,
        indice=0.82
    )

    resultados = listar_todos_os_resultados()
    assert len(resultados) >= 1, "Erro: nenhum registro encontrado"
    print(f"Total de registros encontrados: {len(resultados)}")
    print("Registro de teste:", resultados[-1])
    print("Módulo banco.py verificado com sucesso!")
