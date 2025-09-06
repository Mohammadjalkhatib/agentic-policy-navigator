#Note: All this code runs on aiXplain, where it is deployed.

#!pip install aixplain
#!pip install --quiet pymupdf
#!pip install --upgrade aixplain

import os
import re
from aixplain.modules.model.record import Record
from aixplain.factories import IndexFactory
from aixplain.factories import AgentFactory

# Create a new index
# This index will be the team's knowledge repository
knowledge_index = IndexFactory.create(
    name="Team Knowledge Repository",
    description="A central repository for storing and retrieving long texts and documents shared by the agent team."
)


from aixplain.factories import AgentFactory

agent = AgentFactory.create(
    name="Knowledge Assistant",
    description="I am a helpful assistant who can answer common questions like 'hello' and 'how are you?' with a polite response. If you ask me about legal rules or laws, I will search the index to provide a factual answer. How can I help you today?",
    tools=[
        AgentFactory.create_model_tool("knowledge_index.id")
    ],
    llm="64d21cbb6eb563074a698ef1"
)


agent.deploy()