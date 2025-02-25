import os
from crewai import Agent, Task, Crew, Process
from cerebras.cloud.sdk import Cerebras
import time
import re
import pypdf  # For PDF handling
from typing import Any, List, Dict, Optional, Union

# Set up Cerebras API key in environment
os.environ["CEREBRAS_API_KEY"] = "csk-xd66p263mxydtddcrmtktknxxpn8nxnvd6pknfx9thxhrkyt"

# Initialize Cerebras client
cerebras_client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))

# Custom LLM wrapper for Cerebras SDK that's compatible with CrewAI
class CerebrasLLM:
    def __init__(self, model_name="llama3.1-8b", temperature=0.7):
        self.client = cerebras_client
        self.model_name = model_name
        self.temperature = temperature
    
    def __call__(
        self,
        prompt: str,
        **kwargs: Any
    ) -> str:
        """Generate a response from Cerebras based on the prompt."""
        try:
            # If the prompt contains instructions to use messages format
            if "messages" in kwargs:
                messages = kwargs.get("messages", [])
            else:
                # Convert plain text prompt to message format
                messages = [{"role": "user", "content": prompt}]
            
            start_time = time.time()
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=kwargs.get("temperature", self.temperature),
            )
            end_time = time.time()
            print(f"Cerebras response time: {end_time - start_time:.2f} seconds")
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Cerebras API: {e}")
            return "Sorry, I couldn't process that request."
    
    def supports_stop_words(self) -> bool:
        """Whether the LLM supports stop words."""
        return True
    
    def supports_functions(self) -> bool:
        """Whether the LLM supports function calling."""
        return False

# Initialize the custom LLM
cerebras_llm = CerebrasLLM(model_name="llama3.1-8b", temperature=0.7)

# Create our specialized agents
script_analyst = Agent(
    role="Script Analyst",
    goal="Extract key production elements from film scripts",
    backstory="As an experienced script supervisor, you can identify all crucial elements in a script that will impact budget, including locations, cast size, props, special effects, and technical requirements.",
    verbose=True,
    allow_delegation=False,
    llm=cerebras_llm
)

budget_creator = Agent(
    role="Production Budget Specialist",
    goal="Create accurate film production budgets based on script elements",
    backstory="With years of experience in film production, you can estimate costs for all aspects of filmmaking including talent, locations, equipment, post-production, and contingencies.",
    verbose=True,
    allow_delegation=False,
    llm=cerebras_llm
)

resource_advisor = Agent(
    role="Production Resource Advisor",
    goal="Suggest cost-effective solutions for production challenges",
    backstory="You're an expert at finding creative solutions to production challenges while maintaining quality and staying within budget constraints.",
    verbose=True,
    allow_delegation=False,
    llm=cerebras_llm
)


def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    try:
        # Create a PDF reader object
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        
        # Extract text from each page
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
            
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None


def script_to_budget(script_content, budget_level="low"):
    """
    Process a script and generate a production budget.

    Args:
        script_content (str): The film script content
        budget_level (str): "low", "medium", or "high" indicating budget constraints

    Returns:
        dict: Complete budget breakdown
    """
    # Define tasks for our agents
    script_analysis_task = Task(
        description=f"""
        Analyze the following script and extract ALL production elements that will impact the budget:
        - Number and names of unique characters
        - All locations (interior and exterior)
        - Time periods/eras
        - Special props or set pieces
        - Special effects (practical and digital)
        - Stunts or action sequences
        - Animals or unusual casting requirements
        - Weather conditions or time of day requirements
        - Any other special requirements

        SCRIPT:
        {script_content}

        Provide a comprehensive list of ALL elements organized by category.
        """,
        expected_output="A comprehensive list of all production elements organized by category.",
        agent=script_analyst
    )

    budget_creation_task = Task(
        description=f"""
        Create a detailed production budget for a {budget_level}-budget film based on the script analysis.

        Include line items for:
        1. Pre-production costs
        2. Production costs (cast, crew, equipment, locations)
        3. Post-production costs
        4. Contingency

        This is a {budget_level}-budget production, so adjust your estimates accordingly.

        Production Elements:
        {{script_analysis_task.output}}

        IMPORTANT: Format the budget as properly structured markdown tables with clear headers and columns. 
        Use the following format for each section:

        ## [Section Name] (estimated: $X - $Y)
        
        | Item | Cost |
        |------|------|
        | [Item 1] | $[Amount range] |
        | [Item 2] | $[Amount range] |
        
        Ensure all budget items have a corresponding cost estimate in the table.
        Include a final Total Budget table row at the end.
        """,
        expected_output="A detailed production budget with categories, line items, and costs in properly formatted tables.",
        agent=budget_creator,
        dependencies=[script_analysis_task]
    )

    resource_task = Task(
        description=f"""
        Review the proposed budget and provide 3-5 specific suggestions for cost-effective alternatives or creative solutions that could help the production save money while maintaining quality.

        Budget:
        {{budget_creation_task.output}}

        Production Elements:
        {{script_analysis_task.output}}

        Focus on practical, implementable suggestions specific to this script.
        """,
        expected_output="3-5 specific cost-saving suggestions for the production.",
        agent=resource_advisor,
        dependencies=[script_analysis_task, budget_creation_task]
    )

    # Create and run the crew
    film_budget_crew = Crew(
        agents=[script_analyst, budget_creator, resource_advisor],
        tasks=[script_analysis_task, budget_creation_task, resource_task],
        verbose=True,
        process=Process.sequential
    )

    result = film_budget_crew.kickoff()

    return {
        "script_analysis": script_analysis_task.output,
        "budget": budget_creation_task.output,
        "cost_saving_suggestions": resource_task.output
    }


def process_script_file(file_path, budget_level="low"):
    """
    Process a script file (text or PDF) and generate a budget
    
    Args:
        file_path (str): Path to the script file
        budget_level (str): Budget level (low, medium, high)
    
    Returns:
        dict: Budget information
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check file extension
    if file_path.lower().endswith('.pdf'):
        # Process PDF file
        script_content = extract_text_from_pdf(file_path)
        if not script_content:
            raise ValueError("Failed to extract text from PDF file")
    else:
        # Process text file
        with open(file_path, 'r') as f:
            script_content = f.read()
    
    # Generate budget
    return script_to_budget(script_content, budget_level) 