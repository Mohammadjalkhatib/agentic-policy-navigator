#Note: All this code runs on aiXplain, where it is deployed.

#!pip install aixplain
#!pip install --quiet pymupdf
#!pip install --upgrade aixplain

from aixplain.factories import PipelineFactory
from aixplain.enums import DataType
from aixplain.factories import AgentFactory, ModelFactory

# 1. Initialize the pipeline
pipeline = PipelineFactory.init("Executive Order Retrieval Pipeline")

# 2. Create an input node for the executive order number
order_number_input = pipeline.input()
order_number_input.label = "Executive Order Number Input"

# 3. Add a node to search for PDF URLs
search_node = pipeline.asset(asset_id="get_executive_order_pdf_url.id")
search_node.label = "Search for PDF URL"

# 4. Add a node to extract text from PDF
extract_node = pipeline.asset(asset_id="extract_text_from_pdf_url.id")
extract_node.label = "Extract Text from PDF"

# 5. Add an LLM node for text processing
llm_node = pipeline.text_generation(asset_id="669a63646eb56306647e1091")
llm_node.label = "Generate Client-Friendly Response"

# 6. Connect the nodes (The Correct Method)
# Link the order number input to the search node
order_number_input.outputs.input.link(search_node.inputs.order_number)

# Link the search node outputs to the extract node inputs
search_node.outputs.outputs.link(extract_node.inputs.pdf_url)

# Link the extract node outputs to the LLM node inputs
extract_node.outputs.outputs.link(llm_node.inputs.text)

# 7. Define the pipeline output
llm_node.use_output("data")

# 8. Validate the pipeline
pipeline.validate()

# 9. Save the pipeline
pipeline.save(save_as_asset=True)

print(f"Pipeline created successfully! ID: {pipeline.id}")


pipeline.deploy()

pipeline = PipelineFactory.get("pipeline.id")

pipeline_tool = AgentFactory.create_pipeline_tool(
    pipeline=pipeline.id,
    description="Executive Order Bringer"
)