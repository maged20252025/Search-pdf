
import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import zipfile
import re
from collections import defaultdict

st.set_page_config(page_title="البحث في ملفات PDF (نصي أو صورة)", layout="wide")
st.title("📄 البحث داخل ملفات PDF - يدعم النص والصورة")

# تنظيف وتوحيد النص العربي
def normalize_text(text):
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه")
    return text.strip()

# استخراج النص من صورة باستخدام OCR
def extract_text_with_ocr(page):
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img, lang="ara+eng")
    return text

# تمييز الكلمة داخل النص
def highlight_word(text, word):
    pattern = re.compile(re.escape(word), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark style='background-color: #fff176'>{m.group(0)}</mark>", text)

uploaded_files = st.file_uploader("📤 ارفع ملفات PDF فقط (حتى 50 ملف)", type=["pdf"], accept_multiple_files=True)

keywords_input = st.text_area("✍️ أدخل كلمات البحث (افصل بينها بفاصلة)", "")
search_btn = st.button("🔍 بدء البحث")

if uploaded_files and search_btn and keywords_input.strip():
    raw_keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    normalized_keywords = [normalize_text(k) for k in raw_keywords]

    results = []
    matched_files = {}
    word_counts = defaultdict(int)

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        try:
            pdf = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")
        except:
            st.error(f"❌ تعذر فتح الملف: {file_name}")
            continue

        for page in pdf:
            text = page.get_text()

            # إن لم يوجد نص، نلجأ لـ OCR
            if not text.strip():
                text = extract_text_with_ocr(page)

            lines = [line.strip() for line in text.split("\n") if line.strip()]

            for line in lines:
                norm_line = normalize_text(line)
                for raw_kw, norm_kw in zip(raw_keywords, normalized_keywords):
                    if norm_kw in norm_line:
                        word_counts[raw_kw] += 1
                        highlighted = highlight_word(line, raw_kw)
                        results.append({"file": file_name, "text": highlighted})
                        matched_files[file_name] = file_bytes

    if results:
        st.success(f"✅ تم العثور على {len(results)} نتيجة في {len(matched_files)} ملف.")
        st.markdown("---")

        st.subheader("📊 إحصائيات الكلمات:")
        for word, count in word_counts.items():
            st.write(f"🔹 '{word}': {count} مرة")

        st.markdown("---")
        st.subheader("📄 النتائج:")
        for res in results:
            st.write(f"📘 **الملف:** {res['file']}")
            st.markdown(res["text"], unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("⬇️ تحميل الملفات التي ظهرت فيها نتائج:")

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
