import os
from crewai import Agent, Task, Crew, Process
from cerebras.cloud.sdk import Cerebras
import time
import re

# Set up Cerebras client
os.environ["CEREBRAS_API_KEY"] = "csk-xd66p263mxydtddcrmtktknxxpn8nxnvd6pknfx9thxhrkyt"
cerebras_client = Cerebras()


# Custom LLM tool that uses Cerebras API
class CerebrasLLM:
    def __init__(self, model="llama3.1-8b"):
        self.client = cerebras_client
        self.model = model

    def __call__(self, prompt):
        try:
            # Measure response time
            start_time = time.time()

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
            )

            end_time = time.time()
            print(f"Cerebras response time: {end_time - start_time:.2f} seconds")

            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Cerebras API: {e}")
            return "Sorry, I couldn't process that request."


# Initialize our custom LLM
cerebras_llm = CerebrasLLM()

# Create our specialized agents
script_analyst = Agent(
    role="Script Analyst",
    goal="Extract key production elements from film scripts",
    backstory="As an experienced script supervisor, you can identify all crucial elements in a script that will impact budget, including locations, cast size, props, special effects, and technical requirements.",
    tools=[],
    llm=cerebras_llm,
    verbose=True
)

budget_creator = Agent(
    role="Production Budget Specialist",
    goal="Create accurate film production budgets based on script elements",
    backstory="With years of experience in film production, you can estimate costs for all aspects of filmmaking including talent, locations, equipment, post-production, and contingencies.",
    tools=[],
    llm=cerebras_llm,
    verbose=True
)

resource_advisor = Agent(
    role="Production Resource Advisor",
    goal="Suggest cost-effective solutions for production challenges",
    backstory="You're an expert at finding creative solutions to production challenges while maintaining quality and staying within budget constraints.",
    tools=[],
    llm=cerebras_llm,
    verbose=True
)


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


# Example usage
if __name__ == "__main__":
    # Example script snippet
    sample_script = """
    Title: THE LAST LIGHT

    FADE IN:

    EXT. ABANDONED LIGHTHOUSE - SUNSET

    Waves crash against jagged rocks. A dilapidated lighthouse stands alone on a small island, its light no longer functioning.

    SARAH (35, weathered, determined) approaches in a small motorboat. She ties the boat to a rickety dock and steps onto the island, carrying a backpack.

    SARAH
    (looking up at the lighthouse)
    So this is where it all ends.

    INT. LIGHTHOUSE - GROUND FLOOR - MOMENTS LATER

    Sarah enters the dusty interior. Cobwebs hang from the ceiling. Old furniture is covered in sheets. She touches an old photograph on the wall.

    FLASHBACK - INT. SAME LIGHTHOUSE - 20 YEARS EARLIER - DAY

    YOUNG SARAH (15) laughs with her FATHER (40s), as he shows her how to operate the lighthouse light.

    FATHER
    One day this will all be yours to protect.

    BACK TO PRESENT

    Sarah climbs the spiral staircase to the top of the lighthouse.

    EXT. LIGHTHOUSE TOP - NIGHT

    Sarah works on repairing the old light mechanism by flashlight. As she connects the final wire, the massive light sputters to life, sending a beam across the dark ocean.

    In the distance, a small boat changes course, heading toward the lighthouse.

    FADE OUT.
    """

    # Process the script to generate a budget
    result = script_to_budget(sample_script, budget_level="low")

    print("\n===== SCRIPT ANALYSIS =====")
    print(result["script_analysis"])

    print("\n===== PRODUCTION BUDGET =====")
    print(result["budget"])

    print("\n===== COST-SAVING SUGGESTIONS =====")
    print(result["cost_saving_suggestions"])