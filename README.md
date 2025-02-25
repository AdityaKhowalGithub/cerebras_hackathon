# Script Budget Analyzer

A tool to analyze scripts and generate production budgets using the Cerebras AI API.

## Features

- Analyze scripts from PDF or text files
- Extract production elements that impact budget
- Generate detailed production budgets based on script analysis
- Provide cost-saving suggestions
- Standalone Python script that works with the Cerebras API directly
- Shell script wrapper for easier usage

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make the shell script executable (optional):
   ```
   chmod +x script_budget.sh
   ```

## Usage

### Using the Python Script

```bash
# Process a PDF script with default low budget
python pdf_script_analyzer.py -f your_script.pdf

# Process a PDF script with medium budget
python pdf_script_analyzer.py -f your_script.pdf -b medium

# Process a PDF script with high budget and save output to file
python pdf_script_analyzer.py -f your_script.pdf -b high -o budget_output.txt

# Process a text file
python pdf_script_analyzer.py -f your_script.txt -b low

# Interactive mode (manually paste script)
python pdf_script_analyzer.py
```

### Using the Shell Script Wrapper

```bash
# Make the script executable (if not already done)
chmod +x script_budget.sh

# Process a PDF script with default low budget
./script_budget.sh -f your_script.pdf

# Process a PDF script with medium budget
./script_budget.sh -f your_script.pdf -b medium

# Process a PDF script with high budget and save output to file
./script_budget.sh -f your_script.pdf -b high -o budget_output.txt

# Show help information
./script_budget.sh --help
```

## Command Line Arguments

- `--file`, `-f`: Path to script file (text or PDF)
- `--budget`, `-b`: Budget level (`low`, `medium`, `high`). Default: `low`
- `--output`, `-o`: Output file for the budget (default: print to console)

## Output

The script generates:

1. **Script Analysis**: A detailed breakdown of production elements including characters, locations, special effects, etc.
2. **Production Budget**: A detailed budget with line items for pre-production, production, post-production, and contingency.
3. **Cost-Saving Suggestions**: Practical suggestions for reducing costs while maintaining quality.

## Dependencies

- cerebras-cloud-sdk: For AI-powered script analysis
- pypdf: For PDF file processing
- argparse: For command-line argument parsing

## License

MIT 