"""
Utilitários para gerenciamento de arquivos temporários do FIDC Calculator.
"""

import os
import tempfile
from pathlib import Path


def obter_pasta_uploads() -> str:
    """
    Retorna a pasta temporária usada para armazenar uploads originais.
    """
    pasta = Path(tempfile.gettempdir()) / "fidc_calculator" / "uploads"
    pasta.mkdir(parents=True, exist_ok=True)
    return str(pasta)


def obter_pasta_parquet() -> str:
    """
    Retorna a pasta temporária usada para armazenar bases convertidas em Parquet.
    """
    pasta = Path(tempfile.gettempdir()) / "fidc_calculator" / "parquet"
    pasta.mkdir(parents=True, exist_ok=True)
    return str(pasta)


def salvar_upload_temporario(uploaded_file) -> str:
    """
    Salva o arquivo recebido pelo Streamlit em disco e retorna seu caminho.
    """
    pasta_uploads = obter_pasta_uploads()
    caminho_arquivo = os.path.join(pasta_uploads, uploaded_file.name)

    with open(caminho_arquivo, "wb") as arquivo_destino:
        arquivo_destino.write(uploaded_file.getbuffer())

    return caminho_arquivo


def gerar_caminho_parquet(nome_arquivo_original: str) -> str:
    """
    Gera o caminho do arquivo Parquet correspondente ao Excel original.
    """
    pasta_parquet = obter_pasta_parquet()

    nome_sem_extensao = os.path.splitext(nome_arquivo_original)[0]
    nome_parquet = f"{nome_sem_extensao}.parquet"

    return os.path.join(pasta_parquet, nome_parquet)


def remover_arquivo_se_existir(caminho_arquivo: str) -> None:
    """
    Remove um arquivo, caso ele exista.
    """
    if caminho_arquivo and os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)

def obter_pasta_correcao() -> str:
    """
    Retorna a pasta temporária usada para armazenar
    os resultados da etapa de correção.
    """
    pasta = Path(tempfile.gettempdir()) / "fidc_calculator" / "correcao"
    pasta.mkdir(parents=True, exist_ok=True)
    return str(pasta)


def gerar_caminho_parquet_correcao(nome_base: str) -> str:
    """
    Gera o caminho do arquivo Parquet de resultado da etapa de correção.
    """
    pasta_correcao = obter_pasta_correcao()
    return os.path.join(pasta_correcao, f"{nome_base}.parquet")