import streamlit as st
import pdf2image
from PIL import Image
import pytesseract
from pytesseract import Output, TesseractError
from functions import convert_pdf_to_txt_pages, convert_pdf_to_txt_file, save_pages, displayPDF, images_to_txt
from transformers import pipeline

st.set_page_config(page_title="PDF to Text")


html_temp = """
            <div style="background-color:{};padding:1px">
            
            </div>
            """

# st.markdown("""
#     ## :outbox_tray: Text data extractor: PDF to Text
    
# """)
# st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"),unsafe_allow_html=True)
st.markdown("""
    ## Text data extractor: PDF to Text
    
""")
languages = {
    'English': 'eng',
    'French': 'fra',
    'Arabic': 'ara',
    'Spanish': 'spa',
}

with st.sidebar:
    st.title(":outbox_tray: PDF to Text")
    textOutput = st.selectbox(
        "How do you want your output text?",
        ('One text file (.txt)', 'Text file per page (ZIP)'))
    ocr_box = st.checkbox('Enable OCR (scanned document)')
    
    st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"),unsafe_allow_html=True)
    st.markdown("""
    # How does it work?
    Simply load your PDF and convert it to single-page or multi-page text.
    """)
    st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"),unsafe_allow_html=True)
    st.markdown("""
    Made by [@nainia_ayoub](https://twitter.com/nainia_ayoub) 
    """)
    st.markdown(
        """
        <a href="https://www.buymeacoffee.com/nainiayoub" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174">
        </a>
        """,
        unsafe_allow_html=True,
    )
    

pdf_file = st.file_uploader("Load your PDF", type=['pdf', 'png', 'jpg'])
hide="""
<style>
footer{
	visibility: hidden;
    	position: relative;
}
.viewerBadge_container__1QSob{
  	visibility: hidden;
}
#MainMenu{
	visibility: hidden;
}
<style>
"""
st.markdown(hide, unsafe_allow_html=True)

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_summarizer()

def get_summary(text):
    # Split text into chunks of 1024 tokens for the summarizer
    max_chunk = 1024
    texts = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
    summaries = []
    for chunk in texts:
        if len(chunk) > 100:  # Only summarize chunks with substantial content
            summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
    return " ".join(summaries)

if pdf_file:
    path = pdf_file.read()
    file_extension = pdf_file.name.split(".")[-1]
    
    # Initialize language option early
    option = 'English'  # default language
    
    if file_extension == "pdf":
        # display document
        with st.expander("Preview Document"):
            displayPDF(path)
            
        # Get language selection if OCR is enabled
        if ocr_box:
            option = st.selectbox('Select document language', list(languages.keys()))
        
        # Extract text first
        if ocr_box:
            texts, nbPages = images_to_txt(path, languages[option])
            text_data_f = "\n\n".join(texts)
        else:
            text_data_f, nbPages = convert_pdf_to_txt_file(pdf_file)
        
        # Display extracted text
        st.markdown("""
        <div style='background-color: #f5f5f7; padding: 1.5rem; border-radius: 12px; margin-top: 2rem;'>
        <h3>Extracted Text</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Show Extracted Text"):
            st.text_area("", value=text_data_f, height=300, disabled=True)
        
        # Add summarize button
        if st.button("📝 Generate Summary", help="Generate a summary of the extracted text"):
            with st.spinner("Generating summary..."):
                try:
                    summary = get_summary(text_data_f)
                    st.markdown("""
                    <div style='background-color: #f5f5f7; padding: 1.5rem; border-radius: 12px; margin-top: 2rem;'>
                    <h3>Summary</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.info(summary)
                except Exception as e:
                    st.error("Error generating summary. Text might be too short or invalid.")
        
        # Download buttons in a row
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("⬇️ Download Full Text", text_data_f)
        
        if textOutput == 'One text file (.txt)':
            st.download_button("Download txt file", text_data_f)
        else:
            if ocr_box:
                text_data, nbPages = images_to_txt(path, languages[option])
                totalPages = "Pages: "+str(nbPages)+" in total"
            else:
                text_data, nbPages = convert_pdf_to_txt_pages(pdf_file)
                totalPages = "Pages: "+str(nbPages)+" in total"
            st.info(totalPages)
            zipPath = save_pages(text_data)
            # download text data   
            with open(zipPath, "rb") as fp:
                btn = st.download_button(
                    label="Download ZIP (txt)",
                    data=fp,
                    file_name="pdf_to_txt.zip",
                    mime="application/zip"
                )
    else:
        # Image processing
        option = st.selectbox("Select image language", list(languages.keys()))
        pil_image = Image.open(pdf_file)
        text = pytesseract.image_to_string(pil_image, lang=languages[option])
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("Display Image"):
                st.image(pdf_file)
        with col2:
            with st.expander("Display Text"):
                st.info(text)
        st.download_button("Download txt file", text)

        st.markdown("""
        <div style='background-color: rgb(38, 39, 48); padding: 1.5rem; border-radius: 12px; margin-top: 2rem;'>
        <h3>Extracted Text</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Show Extracted Text"):
            st.text_area("", value=text, height=300, disabled=True)
        
        if st.button("📝 Generate Summary"):
            with st.spinner("Generating summary..."):
                try:
                    summary = get_summary(text)
                    st.markdown("""
                    <div style='background-color: rgb(38, 39, 48); padding: 1.5rem; border-radius: 12px; margin-top: 2rem;'>
                    <h3>Summary</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.info(summary)
                except Exception as e:
                    st.error("Error generating summary. Text might be too short or invalid.")
