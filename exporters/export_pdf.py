"""
pdf_exporter.py

Exporta DataFrames para PDF usando ReportLab.

Autor: Matheus
"""

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def export_to_pdf(df: pd.DataFrame, output_path: str, title: str = "Relatório de Dados"):
    """
    Exporta um DataFrame para PDF com formatação profissional.
    
    Args:
        df: DataFrame a ser exportado
        output_path: Caminho do arquivo PDF de saída
        title: Título do relatório
    """
    
    # Limita a 100 linhas para evitar PDFs gigantes
    MAX_ROWS = 100
    if len(df) > MAX_ROWS:
        df = df.head(MAX_ROWS)
        truncated = True
    else:
        truncated = False
    
    # Configura o documento
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1*cm,
        rightMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Estilo
    styles = getSampleStyleSheet()
    elements = []
    
    # Título
    title_paragraph = Paragraph(f"<b>{title}</b>", styles['Title'])
    elements.append(title_paragraph)
    elements.append(Spacer(1, 0.5*cm))
    
    # Informações do DataFrame
    info_text = f"<b>Total de linhas:</b> {len(df)} | <b>Total de colunas:</b> {len(df.columns)}"
    if truncated:
        info_text += f" <i>(Exibindo apenas as primeiras {MAX_ROWS} linhas)</i>"
    
    info_paragraph = Paragraph(info_text, styles['Normal'])
    elements.append(info_paragraph)
    elements.append(Spacer(1, 0.3*cm))
    
    # Prepara dados da tabela
    data = [list(df.columns)]  # Header
    
    for idx, row in df.iterrows():
        data.append([str(val)[:50] for val in row])  # Limita tamanho do texto
    
    # Cria tabela
    table = Table(data)
    
    # Estilo da tabela
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Corpo da tabela
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    
    # Gera PDF
    doc.build(elements)
    
    print(f"✅ PDF exportado com sucesso: {output_path}")