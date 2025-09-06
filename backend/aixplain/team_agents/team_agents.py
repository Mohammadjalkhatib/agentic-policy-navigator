#Note: All this code runs on aiXplain, where it is deployed.

#!pip install aixplain
#!pip install --quiet pymupdf
#!pip install --upgrade aixplain

import requests
from aixplain.enums import DataType
from aixplain.factories import PipelineFactory
from aixplain.factories import ModelFactory
from aixplain.modules import Pipeline
from aixplain.factories import AgentFactory, TeamAgentFactory

from aixplain.factories import AgentFactory, TeamAgentFactory

try:
    # Retrieve agent objects first
    print("Retrieving individual agents...")
    agent1 = AgentFactory.get("agent1.id")
    agent2 = AgentFactory.get("agent2.id")
    
    print(f"Agent 1 retrieved: {agent1.name}")
    print(f"Agent 2 retrieved: {agent2.name}")
    
    # Create the team
    print("\nCreating the agent team...")
    team = TeamAgentFactory.create(
        name="Policy Navigator Team",
        description="A multi-agent system for navigating government regulations with intelligent workflow:\n\n"
                    "1. LOCAL SEARCH FIRST: When asked about executive orders or regulations, the team first uses the Policy Document Indexer (Agent 1) to search through the internal knowledge base of indexed government documents.\n\n"
                    "2. EXTERNAL API FALLBACK: If no relevant information is found locally, the team automatically activates the Federal Register Search Agent (Agent 2) to query the Federal Register API for the latest status and details.\n\n"
                    "3. APPROPRIATE RESPONSES: For general greetings (e.g., 'Hello', 'Hi there') or help requests (e.g., 'I need help', 'How does this work?'), the system responds with friendly, helpful messages that explain its capabilities and provide examples of questions it can answer.\n\n"
                    "4. CLEAR COMMUNICATION: All responses are delivered in plain language (avoiding legal jargon), include source references when available, and clearly indicate whether information comes from internal knowledge or external APIs.\n\n"
                    "This workflow ensures efficient resource usage while providing accurate, up-to-date information about government regulations and executive orders as required by the Certification-Course-Project.pdf specifications.",
        agents=[agent1, agent2],
        supervisor_llm="669a63646eb56306647e1091",
        use_mentalist=True,
        inspector=True,
    )
except Exception as e:
    print(f"An error occurred: {e}")




team.deploy()
