#Note: All this code runs on aiXplain, where it is deployed.

#!pip install aixplain
#!pip install --quiet pymupdf
#!pip install --upgrade aixplain

from aixplain.enums import DataType
from aixplain.factories import AgentFactory, ModelFactory

def extract_text_from_pdf_url(pdf_url: str) -> str:
    """
    A function that takes a PDF file URL and returns extracted text.
    """
    import requests
    import fitz  # PyMuPDF library
    import io

    try:
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()

        pdf_stream = io.BytesIO(response.content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        text = ""
        for page in doc:
            text += page.get_text() + "\n"

        return text.strip()

    except requests.exceptions.RequestException as e:
        return f"Error loading file: {e}"
    except Exception as e:
        return f"Error reading PDF file: {e}"


extract_text_utility = ModelFactory.create_utility_model(
    name="PDFTextExtractor",
    code=extract_text_from_pdf_url,
    description="Extracts all text from a PDF file using its URL."
)


extract_text_utility.deploy()