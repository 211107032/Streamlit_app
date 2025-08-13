import streamlit as st
from wordcloud import WordCloud, STOPWORDS
import pandas as pd
import PyPDF2
import docx
from io import BytesIO
import re

# Function to read text from different file types
def read_file(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    elif file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return ""

# Sidebar options
st.sidebar.header("Settings")
use_stopwords = st.sidebar.checkbox("Use standard stopwords", value=True)
resolution = st.sidebar.slider("Select resolution (1-100)", 1, 100, 50)

# File upload
uploaded_file = st.file_uploader("Upload a PDF, TXT, or DOCX file", type=["pdf", "txt", "docx"])
if uploaded_file:
    file_details = {
        "filename": uploaded_file.name,
        "filetype": uploaded_file.type,
        "filesize": f"{uploaded_file.size / 1024:.2f} KB"
    }
    st.json(file_details)

    text = read_file(uploaded_file)
    st.subheader("Extracted Text Preview")
    st.write(text[:500] + "..." if len(text) > 500 else text)

    # Get word frequency for suggestions
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = pd.Series(words).value_counts()
    common_words = word_counts.index.tolist()

    # Sidebar additional stopwords with suggestions
    additional_stopwords = st.sidebar.multiselect(
        "Additional stopwords (select to exclude from WordCloud)",
        options=common_words[:50]  # top 50 frequent words
    )

    # Combine stopwords
    stopwords = set(STOPWORDS) if use_stopwords else set()
    stopwords.update(additional_stopwords)

    # File format selection
    file_format = st.selectbox("Select output format", ["png", "jpeg", "webp"])

    # Generate word cloud
    if st.button("Generate Word Cloud"):
        wc = WordCloud(stopwords=stopwords, width=800, height=400, background_color="white").generate(text)
        st.image(wc.to_array())

        # Save as file
        img_buffer = BytesIO()
        wc.to_image().save(img_buffer, format=file_format.upper())
        st.download_button("Save Word Cloud", img_buffer.getvalue(), f"wordcloud.{file_format}", f"image/{file_format}")

        # Show word count table
        st.subheader("Word Count Table")
        wc_table = pd.DataFrame({"Word": word_counts.index, "Count": word_counts.values})
        st.dataframe(wc_table)
        csv = wc_table.to_csv(index=False).encode()
        st.download_button("Download Word Count CSV", csv, "word_count.csv", "text/csv")
