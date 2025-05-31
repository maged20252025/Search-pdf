
import streamlit as st
import os
import fitz  # PyMuPDF
import pdfplumber
from typing import List
import re

st.set_page_config(page_title="بحث داخل ملفات PDF", layout="wide")
st.title("🔍 أداة البحث الذكي داخل ملفات PDF")

uploaded_files = st.file_uploader("📂 ارفع ملفات PDF", type="pdf", accept_multiple_files=True)

search_query = st.text_input("🔎 أدخل كلمة البحث")

def extract_text_from_fitz(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception:
        return ""

def extract_text_from_pdfplumber(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception:
        return ""

def highlight_matches(text: str, query: str) -> List[str]:
    pattern = re.compile(rf"(.{{0,30}})({re.escape(query)})(.{{0,30}})", re.IGNORECASE)
    matches = pattern.findall(text)
    results = []
    for before, match, after in matches:
        snippet = before + f'<mark>{match}</mark>' + after
        results.append(snippet)
    return results

if uploaded_files and search_query:
    for file in uploaded_files:
        with open(file.name, "wb") as f:
            f.write(file.read())

        # جرب PyMuPDF أولاً
        text = extract_text_from_fitz(file.name)
        if not text:
            # fallback إلى pdfplumber
            text = extract_text_from_pdfplumber(file.name)

        matches = highlight_matches(text, search_query)

        if matches:
            st.subheader(f"📄 {file.name}")
            st.write(f"عدد النتائج: {len(matches)}")
            for m in matches:
                st.markdown(m, unsafe_allow_html=True)
