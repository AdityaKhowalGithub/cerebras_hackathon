#!/usr/bin/env python3
import os
import sys
import argparse
import tempfile
from cerebras.cloud.sdk import Cerebras
import time
import pypdf

# Set up Cerebras API key
API_KEY = "csk-xd66p263mxydtddcrmtktknxxpn8nxnvd6pknfx9thxhrkyt"
os.environ["CEREBRAS_API_KEY"] = API_KEY

# Initialize Cerebras client
cerebras_client = Cerebras(api_key=API_KEY)


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


def get_script_analysis(script_content):
    """Get script analysis from Cerebras API"""
    prompt = f"""
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
    """
    
    start_time = time.time()
    response = cerebras_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3.1-8b",
    )
    end_time = time.time()
    print(f"Cerebras response time (Script Analysis): {end_time - start_time:.2f} seconds")
    
    return response.choices[0].message.content


def get_budget(script_analysis, budget_level):
    """Get production budget from Cerebras API"""
    prompt = f"""
    Create a detailed production budget for a {budget_level}-budget film based on the script analysis.

    Include line items for:
    1. Pre-production costs
    2. Production costs (cast, crew, equipment, locations)
    3. Post-production costs
    4. Contingency

    This is a {budget_level}-budget production, so adjust your estimates accordingly.

    Production Elements:
    {script_analysis}

    IMPORTANT: Format the budget as properly structured markdown tables with clear headers and columns. 
    Use the following format for each section:

    ## [Section Name] (estimated: $X - $Y)
    
    | Item | Cost |
    |------|------|
    | [Item 1] | $[Amount range] |
    | [Item 2] | $[Amount range] |
    
    Ensure all budget items have a corresponding cost estimate in the table.
    Include a final Total Budget table row at the end.
    """
    
    start_time = time.time()
    response = cerebras_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3.1-8b",
    )
    end_time = time.time()
    print(f"Cerebras response time (Budget Creation): {end_time - start_time:.2f} seconds")
    
    return response.choices[0].message.content


def get_cost_saving_suggestions(script_analysis, budget):
    """Get cost-saving suggestions from Cerebras API"""
    prompt = f"""
    Review the proposed budget and provide 3-5 specific suggestions for cost-effective alternatives or creative solutions that could help the production save money while maintaining quality.

    Budget:
    {budget}

    Production Elements:
    {script_analysis}

    Focus on practical, implementable suggestions specific to this script.
    """
    
    start_time = time.time()
    response = cerebras_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3.1-8b",
    )
    end_time = time.time()
    print(f"Cerebras response time (Cost Saving Suggestions): {end_time - start_time:.2f} seconds")
    
    return response.choices[0].message.content


def process_script(script_content, budget_level="low"):
    """Process a script and generate a complete budget analysis"""
    print("\nProcessing script...")
    print(f"Budget level: {budget_level}")
    
    # Get script analysis
    print("\nGenerating script analysis...")
    script_analysis = get_script_analysis(script_content)
    
    # Get budget
    print("\nGenerating production budget...")
    budget = get_budget(script_analysis, budget_level)
    
    # Get cost-saving suggestions
    print("\nGenerating cost-saving suggestions...")
    cost_saving_suggestions = get_cost_saving_suggestions(script_analysis, budget)
    
    return {
        "script_analysis": script_analysis,
        "budget": budget,
        "cost_saving_suggestions": cost_saving_suggestions
    }


def process_script_file(file_path, budget_level="low"):
    """Process a script file (text or PDF)"""
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check file extension
    if file_path.lower().endswith('.pdf'):
        # Process PDF file
        print(f"Reading PDF file: {file_path}")
        script_content = extract_text_from_pdf(file_path)
        if not script_content:
            raise ValueError("Failed to extract text from PDF file")
    else:
        # Process text file
        print(f"Reading text file: {file_path}")
        with open(file_path, 'r') as f:
            script_content = f.read()
    
    # Process script
    return process_script(script_content, budget_level)


def save_to_file(file_path, result):
    """Save results to a file"""
    with open(file_path, 'w') as f:
        f.write("===== SCRIPT ANALYSIS =====\n\n")
        f.write(result["script_analysis"])
        f.write("\n\n===== PRODUCTION BUDGET =====\n\n")
        f.write(result["budget"])
        f.write("\n\n===== COST-SAVING SUGGESTIONS =====\n\n")
        f.write(result["cost_saving_suggestions"])


def main():
    parser = argparse.ArgumentParser(description='Convert a script (text or PDF) into a production budget')
    parser.add_argument('--file', '-f', type=str, help='Path to script file (text or PDF)')
    parser.add_argument('--budget', '-b', type=str, choices=['low', 'medium', 'high'],
                        default='low', help='Budget level (default: low)')
    parser.add_argument('--output', '-o', type=str, help='Output file for the budget (default: print to console)')

    args = parser.parse_args()

    # Handle script input
    script_content = ""
    if args.file:
        try:
            # Process the script file
            result = process_script_file(args.file, args.budget)
            
            # Output the results
            if args.output:
                save_to_file(args.output, result)
                print(f"\nBudget saved to {args.output}")
            else:
                print("\n===== SCRIPT ANALYSIS =====\n")
                print(result["script_analysis"])
                print("\n===== PRODUCTION BUDGET =====\n")
                print(result["budget"])
                print("\n===== COST-SAVING SUGGESTIONS =====\n")
                print(result["cost_saving_suggestions"])
                
            return
        except Exception as e:
            print(f"Error processing script file: {e}")
            sys.exit(1)
    else:
        print("Enter your script content (type 'END' on a new line when finished):")
        while True:
            line = input()
            if line.strip() == "END":
                break
            script_content += line + "\n"

    if not script_content.strip():
        print("Error: No script content provided.")
        sys.exit(1)

    # Process the script from input
    result = process_script(script_content, args.budget)

    # Output the results
    if args.output:
        save_to_file(args.output, result)
        print(f"Budget saved to {args.output}")
    else:
        print("\n===== SCRIPT ANALYSIS =====\n")
        print(result["script_analysis"])
        print("\n===== PRODUCTION BUDGET =====\n")
        print(result["budget"])
        print("\n===== COST-SAVING SUGGESTIONS =====\n")
        print(result["cost_saving_suggestions"])


if __name__ == "__main__":
    main() 