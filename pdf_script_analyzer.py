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
    Analyze the following script and extract ALL production elements that will impact the budget.
    Be concise but thorough. Identify:
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

    Provide a focused list of elements organized by category. Be brief but complete.
    """
    
    start_time = time.time()
    response = cerebras_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3.1-8b",
        max_tokens=2048  # Limit response size
    )
    end_time = time.time()
    print(f"Cerebras response time (Script Analysis): {end_time - start_time:.2f} seconds")
    
    return response.choices[0].message.content


def get_budget(script_analysis, budget_level):
    """Get production budget from Cerebras API"""
    prompt = f"""
    Create a detailed production budget for a {budget_level}-budget film based on this script analysis:
    
    {script_analysis}

    Include line items for:
    1. Pre-production costs
    2. Production costs (cast, crew, equipment, locations)
    3. Post-production costs
    4. Contingency

    This is a {budget_level}-budget production, so adjust your estimates accordingly.

    Format the budget as structured markdown tables with clear headers and columns:

    ## [Section Name] (estimated: $X - $Y)
    
    | Item | Cost |
    |------|------|
    | [Item 1] | $[Amount range] |
    | [Item 2] | $[Amount range] |
    
    Include a final Total Budget row at the end.
    """
    
    start_time = time.time()
    response = cerebras_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3.1-8b",
        max_tokens=2048  # Limit response size
    )
    end_time = time.time()
    print(f"Cerebras response time (Budget Creation): {end_time - start_time:.2f} seconds")
    
    return response.choices[0].message.content


def get_cost_saving_suggestions(script_analysis, budget):
    """Get cost-saving suggestions from Cerebras API"""
    prompt = f"""
    Review this proposed budget and provide 3-5 specific suggestions for cost-effective alternatives:
    
    {budget}

    Based on this script analysis:
    {script_analysis}

    Focus on practical, implementable suggestions specific to this production.
    """
    
    start_time = time.time()
    response = cerebras_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3.1-8b",
        max_tokens=2048  # Limit response size
    )
    end_time = time.time()
    print(f"Cerebras response time (Cost Saving Suggestions): {end_time - start_time:.2f} seconds")
    
    return response.choices[0].message.content


def process_script(script_content, budget_level="low"):
    """Process a script and generate a complete budget analysis"""
    print("\nProcessing script...")
    print(f"Budget level: {budget_level}")
    
    # Check if the script is too long and truncate if necessary
    token_estimate = len(script_content.split())
    max_tokens = 2500  # More aggressive truncation - reduced from 4000
    
    if token_estimate > max_tokens:
        print(f"Script is very long ({token_estimate} words). Truncating to approximately {max_tokens} words to fit token limits.")
        # Truncate to approximately max_tokens words
        script_content = " ".join(script_content.split()[:max_tokens])
        script_content += "\n\n[Note: Script was truncated due to length limitations. Analysis is based on this portion only.]"
    
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
        # Process text file - try different encodings
        print(f"Reading text file: {file_path}")
        script_content = None
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16', 'utf-32', 
                   'utf-8-sig', 'windows-1250', 'windows-1251', 'windows-1252', 
                   'windows-1253', 'windows-1254', 'windows-1255', 'windows-1256', 
                   'windows-1257', 'windows-1258']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    script_content = f.read()
                # If successful, break the loop
                print(f"Successfully read file with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                # Try the next encoding
                continue
        
        # If all encodings failed
        if script_content is None:
            try:
                # Try binary mode as a last resort
                with open(file_path, 'rb') as f:
                    binary_data = f.read()
                    
                    # Try to detect if there's a BOM (Byte Order Mark)
                    if binary_data.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
                        script_content = binary_data[3:].decode('utf-8', errors='replace')
                    elif binary_data.startswith(b'\xff\xfe'):  # UTF-16 LE BOM
                        script_content = binary_data[2:].decode('utf-16-le', errors='replace')
                    elif binary_data.startswith(b'\xfe\xff'):  # UTF-16 BE BOM
                        script_content = binary_data[2:].decode('utf-16-be', errors='replace')
                    else:
                        # Try to use chardet if available
                        try:
                            import chardet
                            detected = chardet.detect(binary_data)
                            if detected and detected['encoding'] and detected['confidence'] > 0.5:
                                print(f"Detected encoding: {detected['encoding']} with confidence {detected['confidence']}")
                                script_content = binary_data.decode(detected['encoding'], errors='replace')
                            else:
                                # Last resort: force decode with replace for invalid chars
                                print("Falling back to latin-1 encoding")
                                script_content = binary_data.decode('latin-1', errors='replace')
                        except ImportError:
                            # If chardet is not available, use safe fallback
                            print("Chardet not available, using latin-1 encoding")
                            script_content = binary_data.decode('latin-1', errors='replace')
            except Exception as e:
                print(f"Error in binary fallback: {str(e)}")
                # Absolutely last resort - just replace any non-ASCII bytes with spaces
                print("Using last resort encoding method")
                script_content = ''.join(chr(b) if b < 128 else ' ' for b in binary_data)
    
    # Process script
    return process_script(script_content, budget_level)


def save_to_file(file_path, result):
    """Save results to a file"""
    with open(file_path, 'w', encoding='utf-8') as f:
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