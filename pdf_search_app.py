
import streamlit as st
import fitz  # PyMuPDF
import io
import zipfile
import re

st.set_page_config(page_title="البحث في ملفات PDF فقط", layout="wide")
st.title("📄 البحث داخل ملفات PDF (أحكام فقط)")

# تنظيف النص العربي لتوحيد المقارنة
def normalize_text(text):
    text = re.sub(r"[ًٌٍَُِّْ]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه").replace("ـ", "")
    return text.strip()

# تظليل تكرار واحد فقط باستخدام مواضع start و end
def highlight_exact_hit(text, keyword, match_index):
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    matches = list(pattern.finditer(text))
    if match_index < len(matches):
        match = matches[match_index]
        start, end = match.start(), match.end()
        return (
            text[:start]
            + f"<mark style='background-color: #fff176'>{text[start:end]}</mark>"
            + text[end:]
        )
    return text

uploaded_files = st.file_uploader("📤 ارفع ملفات PDF فقط (حتى 50 ملف)", type=["pdf"], accept_multiple_files=True)

keywords = st.text_area("✍️ الكلمات المفتاحية (افصل كل كلمة بفاصلة)", "")
search_button = st.button("🔍 بدء البحث")

if uploaded_files and search_button:
    raw_keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    keyword_list = [normalize_text(k) for k in raw_keywords]
    results = []
    matched_files = {}

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        pdf = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")
        for page in pdf:
            text = page.get_text()
            if not text.strip():
                continue
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            for line in lines:
                norm_line = normalize_text(line)

                for raw_kw, norm_kw in zip(raw_keywords, keyword_list):
                    pattern = re.compile(rf"\b{re.escape(norm_kw)}\b", re.IGNORECASE)
                    visible_pattern = re.compile(re.escape(raw_kw), re.IGNORECASE)
                    visible_matches = list(visible_pattern.finditer(line))

                    for idx, match in enumerate(visible_matches):
                        highlighted = (
                            line[:match.start()]
                            + f"<mark style='background-color: #fff176'>{line[match.start():match.end()]}</mark>"
                            + line[match.end():]
                        )
                        results.append({
                            "الملف": file_name,
                            "النص": highlighted
                        })
                        matched_files[file_name] = file_bytes

    if results:
        st.success(f"✅ تم العثور على {len(results)} نتيجة في {len(matched_files)} ملف")

        for res in results:
            st.write(f"📘 **الملف:** {res['الملف']}")
            st.markdown(res["النص"], unsafe_allow_html=True)

        st.markdown("---")
        st.header("⬇️ تحميل الملفات التي ظهرت فيها نتائج:")

        for name, content in matched_files.items():
            st.download_button(f"📄 تحميل الملف: {name}", data=content, file_name=name)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for filename, content in matched_files.items():
                zipf.writestr(filename, content)
        zip_buffer.seek(0)

        st.download_button("📦 تحميل جميع الملفات دفعة واحدة (ZIP)", data=zip_buffer, file_name="matched_pdfs.zip")
    else:
        st.warning("لم يتم العثور على أي نتائج.")
