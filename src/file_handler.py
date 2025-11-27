"""
file_handler.py

Funções para leitura e validação de arquivos (CSV, Excel, PDF) e comparação de colunas.
Dependências sugeridas (colocar em requirements.txt):
- pandas
- pdfplumber
- openpyxl

Observações:
- Para PDF: tentamos extrair tabelas com pdfplumber. Se encontrar tabelas, concatenamos em um DataFrame.
  Se não encontrar tabelas, retornamos um DataFrame com uma coluna 'text' contendo o texto extraído por página.
- Para Excel: se houver múltiplas sheets, carregamos a primeira por padrão. Você pode adaptar para pedir
  ao usuário a sheet desejada.

Autores: Matheus (orientação do assistente)
"""

import os
from typing import Tuple, Optional
import pandas as pd

try:
    import pdfplumber
except Exception:
    pdfplumber = None


class FileHandlerError(Exception):
    pass


def detect_file_type(path: str) -> str:
    """Detecta o tipo básico do arquivo a partir da extensão.

    Retorna: 'csv', 'excel', 'pdf' ou 'unknown'.
    """
    _, ext = os.path.splitext(path.lower())
    if ext in ('.csv',):
        return 'csv'
    if ext in ('.xls', '.xlsx'):
        return 'excel'
    if ext in ('.pdf',):
        return 'pdf'
    return 'unknown'


def load_file(path: str, excel_sheet: Optional[str] = None) -> pd.DataFrame:
    """Carrega um arquivo em um pandas.DataFrame.

    Suporta CSV, Excel e PDF (extração de tabelas com pdfplumber).

    Args:
        path: caminho do arquivo
        excel_sheet: nome ou índice da sheet (opcional, para arquivos Excel)

    Returns:
        pd.DataFrame

    Raises:
        FileHandlerError se algo der errado.
    """
    if not path:
        raise FileHandlerError("Caminho vazio recebido para load_file")

    if not os.path.exists(path):
        raise FileHandlerError(f"Arquivo não encontrado: {path}")

    ftype = detect_file_type(path)

    try:
        if ftype == 'csv':
            # Tentativa robusta: detectar encoding automaticamente via pandas (pode falhar em encodings exóticos)
            df = pd.read_csv(path, dtype=str)
            return df

        if ftype == 'excel':
            # Lê a sheet especificada ou a primeira
            df = pd.read_excel(path, sheet_name=excel_sheet, dtype=str)
            # Se for um dict (muitas sheets), pega a primeira
            if isinstance(df, dict):
                first_sheet = list(df.keys())[0]
                df = df[first_sheet]
            return df

        if ftype == 'pdf':
            if pdfplumber is None:
                raise FileHandlerError(
                    "pdfplumber não está instalado. Instale com: pip install pdfplumber"
                )

            tables = []
            texts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    # tenta extrair tabelas
                    page_tables = page.extract_tables()
                    if page_tables:
                        for t in page_tables:
                            # cada tabela é uma lista de linhas (listas)
                            try:
                                df_page = pd.DataFrame(t)
                                # Se primeira linha parece header (todas strings e sem None), promovemos
                                # Ajustes simples: se a primeira linha não contém None e não é numérica, usa como header
                                header_candidate = df_page.iloc[0].tolist()
                                if all(isinstance(h, str) for h in header_candidate):
                                    df_page.columns = header_candidate
                                    df_page = df_page.drop(index=0).reset_index(drop=True)
                                tables.append(df_page)
                            except Exception:
                                continue
                    # coleta texto de fallback
                    page_text = page.extract_text()
                    texts.append(page_text if page_text else "")

            if tables:
                # normaliza colunas e concatena
                # converte colunas para strings
                norm_tables = []
                for t in tables:
                    t.columns = [str(c).strip() for c in t.columns]
                    norm_tables.append(t)
                df_all = pd.concat(norm_tables, ignore_index=True, sort=False).astype(str)
                return df_all
            else:
                # retorna DataFrame com o texto por página
                df_text = pd.DataFrame({'text': texts})
                return df_text

        raise FileHandlerError(f"Tipo de arquivo não suportado: {path}")

    except FileHandlerError:
        raise
    except Exception as e:
        raise FileHandlerError(f"Erro ao carregar arquivo {path}: {e}")


def compare_columns(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[bool, dict]:
    """Compara colunas de dois DataFrames.

    Retorna (is_equal, details) onde details contém:
      - 'only_in_df1': colunas que existem só no df1
      - 'only_in_df2': colunas que existem só no df2
      - 'common': colunas em comum

    A comparação é feita por nome das colunas (caso-sensível). Se quiser case-insensitive,
    normalize os nomes antes (ex.: str.lower()).
    """
    if df1 is None or df2 is None:
        raise FileHandlerError("Um ou ambos DataFrames são None na comparação de colunas")

    cols1 = list(df1.columns)
    cols2 = list(df2.columns)

    set1 = set(cols1)
    set2 = set(cols2)

    only_in_df1 = sorted(list(set1 - set2))
    only_in_df2 = sorted(list(set2 - set1))
    common = sorted(list(set1 & set2))

    is_equal = (len(only_in_df1) == 0) and (len(only_in_df2) == 0)

    details = {
        'only_in_df1': only_in_df1,
        'only_in_df2': only_in_df2,
        'common': common,
        'cols1': cols1,
        'cols2': cols2
    }

    return is_equal, details


if __name__ == '__main__':
    # Pequeno teste manual quando executado direto
    import sys

    if len(sys.argv) < 2:
        print("Uso: python file_handler.py <caminho_para_arquivo>")
        sys.exit(1)

    p = sys.argv[1]
    try:
        df = load_file(p)
        print("Arquivo carregado com sucesso. Colunas:")
        print(df.columns.tolist())
    except FileHandlerError as e:
        print(f"Erro: {e}")
