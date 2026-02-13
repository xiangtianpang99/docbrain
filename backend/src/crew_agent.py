import os
from crewai import Agent, Task, Crew, Process
from src.llm_provider import LLMFactory
from src.config_manager import config_manager
from crewai.tools import tool

class DocBrainCrew:
    def __init__(self, query_engine):
        """
        Initialize the Crew with a reference to the QueryEngine.
        """
        self.query_engine = query_engine
        
        # Initialize LLM using Factory
        try:
             self.llm = LLMFactory.create_crew_llm(config_manager)
        except Exception as e:
             print(f"Error initializing Crew LLM: {e}")
             self.llm = None

    def run_crew(self, query: str) -> str:
        """
        Run the CrewAI process for a complex query.
        """
        print(f"Spawning CrewAI agents for query: {query}")

        # 1. Define the Knowledge Base Tool
        @tool("Search Local Knowledge Base")
        def search_knowledge_base(search_query: str) -> str:
            """
            Search the local knowledge base for relevant information.
            Useful for finding specific facts, documents, or context.
            """
            try:
                # We reuse the existing retrieval logic
                docs = self.query_engine.retrieve_context(search_query, k=5, quality_mode=True)
                if not docs:
                    return "No relevant documents found."
                
                results = []
                for doc in docs:
                    source = doc.metadata.get("source", "Unknown")
                    content = doc.page_content
                    results.append(f"Source: {source}\nContent: {content}")
                
                return "\n\n---\n\n".join(results)
            except Exception as e:
                return f"Error searching knowledge base: {str(e)}"

        # 2. Define Agents
        researcher = Agent(
            role='Senior Researcher',
            goal='Uncover detailed information from the knowledge base to answer the user query completely.',
            backstory="""You are an expert researcher with a keen eye for detail. 
            You are capable of breaking down complex questions into specific search queries 
            to gather all necessary information from the local knowledge base.""",
            verbose=True,
            allow_delegation=False,
            tools=[search_knowledge_base],
            llm=self.llm
        )

        writer = Agent(
            role='Technical Writer',
            goal='Synthesize research findings into a comprehensive, well-structured, and clear answer.',
            backstory="""You are a skilled technical writer. You take raw information and 
            transform it into easy-to-understand, logical, and accurate content. 
            You always cite your sources based on the provided information.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # 3. Define Tasks
        task_research = Task(
            description=f"""
            Analyze the user's request: "{query}"
            1. Break down the request into necessary information components.
            2. Use the 'Search Local Knowledge Base' tool to gather information for each component. 
            3. You may need to search multiple times with different keywords to get a complete picture.
            4. Compile all relevant findings, ensuring source paths are preserved.
            """,
            expected_output="A comprehensive collection of relevant information from the knowledge base, with sources.",
            agent=researcher
        )

        task_write = Task(
            description=f"""
            Using the information gathered by the Researcher, write a final answer to the user's request: "{query}"
            1. Synthesize the findings into a coherent response.
            2. Structure the answer logically (e.g., using headings, bullet points).
            3. Explicitly cite sources (file paths) for key facts.
            4. If information is missing, state what could not be found.
            """,
            expected_output="A detailed, well-structured, and sourced answer to the user's query.",
            agent=writer
        )

        # 4. Create and Run Crew
        crew = Crew(
            agents=[researcher, writer],
            tasks=[task_research, task_write],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()
        return result
