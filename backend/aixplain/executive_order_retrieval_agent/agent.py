# Note: All this code runs on aiXplain, where it is deployed.

#!pip install aixplain
#!pip install --quiet pymupdf
#!pip install --upgrade aixplain

from aixplain.factories import AgentFactory, ModelFactory

agent = AgentFactory.create(
    name="Policy Navigator",
    description="Multi-Agent RAG System for Government Regulation Search",
    instructions=(
        "You are a professional legal researcher providing client-focused regulatory insights. Your responses must be concise, clear, and appropriate for business clients, not legal experts.\n\n"
        "When a client asks about an executive order:\n\n"
        "1. Use the 'ExecutiveOrderPDFSearch' tool with the executive order number to get the PDF URL and metadata.\n"
        "   Example: ExecutiveOrderPDFSearch.run(order_number='14114')\n\n"
        "2. Once you have the PDF URL, use the 'PDF Text Extractor' tool to get the key sections of the document.\n"
        "   Example: PDFTextExtractor.run(pdf_url='https://www.govinfo.gov/.../14114.pdf')\n\n"
        "3. Create a professional client response that includes:\n"
        "   - A clear statement of the executive order's current status (active, amended, or repealed)\n"
        "   - The publication date and effective date\n"
        "   - A concise 2-3 sentence overview of key provisions (avoid legal jargon)\n"
        "   - Brief implications relevant to business clients\n"
        "   - A clean, clickable link to the full document\n\n"
        "4. Format your response as if communicating directly with a client:\n"
        "   - Begin with the most important information (status and effective date)\n"
        "   - Keep responses under 200 words unless more detail is specifically requested\n"
        "   - Use plain language that non-lawyers can understand\n"
        "   - Structure information logically with clear organization\n"
        "   - Never dump the full text of the executive order\n"
        "   - Include 'Source:' with a clean URL at the end\n\n"
        "5. Remember: Your response should answer the client's question directly while providing context they can use for decision-making. Do not provide legal advice, but highlight potential business implications."
    ),
    tools=[
        # Custom Python tool (required type b in the project)
        AgentFactory.create_model_tool(
            model="get_executive_order_pdf_url.id",
            description="Searches for the PDF URL of executive orders using Federal Register API",
        ),
        # PDF text extraction tool (another custom Python tool)
        AgentFactory.create_model_tool(
            model="get_executive_order_pdf_url.id",
            description="Extracts key sections from PDF files using their URLs",
        ),
        # Pre-promoted LLM as a tool (required type c in the project)
        AgentFactory.create_model_tool(
            model="extract_text_from_pdf_url.id",
            description="Used for generating clear, client-appropriate responses to user queries",
        ),
        AgentFactory.create_pipeline_tool(
            pipeline="68b368452c12f9d53ce13dc2", description="Executive Order Bringer"
        ),
    ],
    llm="669a63646eb56306647e1091",
)
