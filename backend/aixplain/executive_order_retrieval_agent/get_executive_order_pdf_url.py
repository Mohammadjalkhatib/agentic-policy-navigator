#Note: All this code runs on aiXplain, where it is deployed.

#!pip install aixplain
#!pip install --quiet pymupdf
#!pip install --upgrade aixplain

from aixplain.enums import DataType
from aixplain.factories import AgentFactory, ModelFactory

def get_executive_order_pdf_url(order_number: str) -> str:
    """
    Find and return ONLY the PDF URL for a specific executive order.
    
    This function searches for executive orders by number using the Federal Register API
    and returns only the cleaned PDF URL with no additional information or whitespace.
    
    Args:
        order_number (str): The executive order number to search for (e.g., "14067")
        
    Returns:
        str: The cleaned PDF URL if found, or an error message
        
    Example:
        >>> get_executive_order_pdf_url("14068")
        "https://www.govinfo.gov/content/pkg/FR-2022-03-15/pdf/2022-05554.pdf"
    """
    import requests
    
    # Clean and validate input
    order_number = str(order_number).strip()
    if not order_number or not order_number.isdigit():
        return f"Error: Invalid executive order number: {order_number}. Must be numeric."
    
    try:
        # Convert to integer for the search
        eo_number = int(order_number)
        
        # Set up the search parameters
        params = {
            "conditions[presidential_document_type]": "executive_order",
            "conditions[type]": "PRESDOCU",
            "conditions[term]": f"\"Executive Order {eo_number}\"",
            "order": "newest",
        }
        
        # Specify the fields we want to retrieve
        fields = [
            "title", "executive_order_number", "pdf_url", "html_url",
            "document_number", "publication_date", "signing_date"
        ]
        for f in fields:
            params.setdefault("fields[]", []).append(f)

        # Clean the API URL
        FR_API = "https://www.federalregister.gov/api/v1/documents.json"
        
        # Make the API request
        response = requests.get(FR_API, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        # Process the results
        candidates = []
        for doc in data.get("results", []):
            num = str(doc.get("executive_order_number") or "").strip()
            title = doc.get("title") or ""
            if num == str(eo_number) or f"Executive Order {eo_number}" in title:
                candidates.append(doc)

        if not candidates:
            return f"Error: No executive order found with number {eo_number}."

        # Get the best match
        best = candidates[0]
        pdf_url = best.get("pdf_url")
        
        # Clean the PDF URL (remove any whitespace)
        if pdf_url:
            # Return ONLY the cleaned URL with no extra spaces or data
            return pdf_url.strip()

        # If no pdf_url, try to construct an alternative URL
        pub_date = best.get("publication_date")
        doc_no = best.get("document_number")
        if pub_date and doc_no:
            alt_pdf_url = f"https://www.govinfo.gov/content/pkg/FR-{pub_date}/pdf/{doc_no}.pdf"
            # Return ONLY the cleaned URL with no extra spaces or data
            return alt_pdf_url.strip()

        return f"Error: Found Executive Order {eo_number} but couldn't generate a PDF link."
        
    except requests.exceptions.RequestException as e:
        return f"Error: Network error connecting to Federal Register API: {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error processing request: {str(e)}"
    
    from aixplain.factories import AgentFactory


from aixplain.factories import AgentFactory

extract_text_utility = ModelFactory.create_utility_model(
    name="find",
    code=get_executive_order_pdf_url,
    description="Extracts all text from a PDF file using its URL."
)

get_executive_order_pdf_url.deploy()