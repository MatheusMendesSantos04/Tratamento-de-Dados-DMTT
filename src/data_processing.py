import pandas as pd
import pdfplumber
from typing import List


# ============================================================
# 1) Ler PDF e transformar em DataFrame
# ============================================================

def load_pdf_as_dataframe(pdf_path: str) -> pd.DataFrame:
    """
    Lê um PDF que contém tabelas e retorna um DataFrame consolidado.
    """
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_table()
            if extracted:
                df = pd.DataFrame(extracted[1:], columns=extracted[0])
                tables.append(df)

    if not tables:
        raise ValueError("Nenhuma tabela foi encontrada no PDF.")

    # Consolida múltiplas tabelas caso existam
    full_df = pd.concat(tables, ignore_index=True)
    return full_df


# ============================================================
# 2) Mostrar colunas disponíveis para o usuário
# ============================================================

def list_columns(df: pd.DataFrame) -> List[str]:
    """
    Retorna a lista de colunas disponíveis no DataFrame.
    """
    return list(df.columns)


# ============================================================
# 3) Permitir seleção de colunas relevantes
# ============================================================

def select_columns(df: pd.DataFrame, selected_columns: List[str]) -> pd.DataFrame:
    """
    Retorna um novo DataFrame contendo apenas as colunas escolhidas.
    """
    missing_cols = [c for c in selected_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(f"As seguintes colunas não existem no PDF: {missing_cols}")

    return df[selected_columns].copy()


# ============================================================
# 4) Preparar dataset para comparação
# ============================================================

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza texto, remove espaços extras, normaliza números
    e prepara o DataFrame para comparações.
    """
    df_clean = df.copy()

    for col in df_clean.columns:
        # Se for texto → padroniza
        if df_clean[col].dtype == "object":
            df_clean[col] = (
                df_clean[col]
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
                .str.lower()
            )

        # Se for número misturado com texto → tenta converter
    try:
        df_clean[col] = pd.to_numeric(
        df_clean[col].astype(str).str.replace(",", "."), 
        errors="coerce"
    )
    except Exception:
        pass

    return df_clean


def fix_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove colunas None, junta colunas quebradas
    e renomeia colunas automaticamente quando necessário.
    """
    df_fixed = df.copy()

    # Remove colunas vazias ou chamadas "None"
    df_fixed = df_fixed[[c for c in df_fixed.columns if c and c.lower() != "none"]]

    # Corrige quebras de linha no nome
    df_fixed.columns = [str(c).replace("\n", " ").strip() for c in df_fixed.columns]

    # Remove duplicações ou colunas muito pequenas
    df_fixed = df_fixed.loc[:, ~df_fixed.columns.duplicated()]

    return df_fixed