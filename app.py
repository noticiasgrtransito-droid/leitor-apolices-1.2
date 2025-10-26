
import re
import io
import pandas as pd
import streamlit as st
import PyPDF2
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

st.set_page_config(page_title="Leitor de Apólices — Extração de Dados em PDF", page_icon="📄")
st.title("📄 Leitor de Apólices — Extração de Dados em PDF")
st.write("Envie um ou mais PDFs e o aplicativo tentará identificar automaticamente os principais campos da apólice (Segurado, Seguradora, Corretora, Vigência, Ramo, LMG etc).")

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text_pages = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            if text:
                text_pages.append((i+1, text))
        except:
            pass
    return text_pages

# Função para buscar padrões
def find_value(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

st.sidebar.header("📤 Upload dos PDFs")
uploaded_files = st.sidebar.file_uploader("Selecione um ou mais arquivos PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    resultados = []
    for uploaded_file in uploaded_files:
        with st.spinner(f"Lendo {uploaded_file.name}..."):
            pages = extract_text_from_pdf(uploaded_file)
            for page_number, text in pages:
                campos = {
                    "Transportadora": r"Transportadora[:\s\-]*([A-Z0-9\s\.\-&]+)",
                    "Seguradora": r"Seguradora[:\s\-]*([A-Z0-9\s\.\-&]+)",
                    "CNPJ Segurado": r"CNPJ.*?(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",
                    "Inicio Vigência Apólice": r"In[íi]cio Vig[eê]ncia[:\s\-]*([0-9/]+)",
                    "Fim Vigência Apólice": r"Fim Vig[eê]ncia[:\s\-]*([0-9/]+)",
                    "Vigência": r"Vig[eê]ncia[:\s\-]*([0-9A-Za-z\s/ até]+)",
                    "NÚMERO SUSEP TRANSPORTADORA": r"Susep[:\s\-]*([0-9]+)",
                    "GRUPO": r"Grupo[:\s\-]*([A-Z0-9\s]+)",
                    "RAMO": r"Ramo[:\s\-]*([A-Z\s]+)",
                    "Código Susep Corretora": r"Susep[:\s\-]*([0-9]+)",
                    "Corretora": r"Corretora[:\s\-]*([A-Z0-9\s\.\-&]+)",
                    "CNPJ Corretora": r"Corretora.*?(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",
                    "Código Susep apólice": r"Susep[:\s\-]*([0-9]+)",
                    "Limite Máximo de Garantia": r"Limite M[aá]ximo.*?([\d\.,]+)",
                    "LMG": r"LMG[:\s\-]*([\d\.,]+)",
                    "Produto de higiene e limpeza, Cosméticos/ Perfumes e artigos de perfumaria": r"(Higiene|Limpeza|Cosm[eé]tico|Perfume|Perfumaria)",
                    "Artigos de higiene e limpeza, Cosméticos/ Perfumes e artigos de perfumaria": r"(Higiene|Limpeza|Cosm[eé]tico|Perfume|Perfumaria)",
                    "CELULAR Transportadora": r"Celular[:\s\-]*([0-9\s\(\)\-]+)",
                    "TELEFONE Transportadora": r"Telefone[:\s\-]*([0-9\s\(\)\-]+)",
                    "Estado": r"Estado[:\s\-]*([A-Z]{2})",
                    "UF": r"UF[:\s\-]*([A-Z]{2})",
                    "ENDEREÇO": r"Endere[cç]o[:\s\-]*([A-Z0-9\s\.,\-]+)",
                    "Email Transportador": r"Email[:\s\-]*([a-z0-9\.\-_]+@[a-z0-9\.\-]+)",
                    "Nome Responsável Transportadora": r"Respons[aá]vel[:\s\-]*([A-Z\s]+)"
                }
                linha = {"Arquivo": uploaded_file.name, "Página": page_number, "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
                for campo, padrao in campos.items():
                    linha[campo] = find_value(padrao, text)
                resultados.append(linha)
    
    df = pd.DataFrame(resultados)
    st.subheader("📊 Resultados extraídos")
    st.dataframe(df, use_container_width=True)

    formato = st.selectbox("Escolha o formato de exportação:", ["CSV (.csv)", "Excel (.xlsx)", "PDF (.pdf)"])
    if formato == "CSV (.csv)":
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"dados_apolices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    elif formato == "Excel (.xlsx)":
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
        st.download_button(
            label="📥 Baixar Excel",
            data=excel_buffer.getvalue(),
            file_name=f"dados_apolices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif formato == "PDF (.pdf)":
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, 550, f"Leitor de Apólices — Extração de Dados em PDF / {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        table.wrapOn(pdf, 800, 600)
        table.drawOn(pdf, 30, 400)
        pdf.save()
        st.download_button(
            label="📥 Baixar PDF (.pdf)",
            data=buffer.getvalue(),
            file_name=f"dados_apolices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
else:
    st.info("📂 Envie um ou mais arquivos PDF para começar a extração.")
