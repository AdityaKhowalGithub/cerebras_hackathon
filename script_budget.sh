#!/bin/bash

# Script Budget Analyzer - Shell Wrapper
# This script provides a convenient way to run the PDF Script Analyzer

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.x to use this script."
    exit 1
fi

# Check if required packages are installed
if ! python -c "import pypdf, cerebras" &> /dev/null; then
    echo "Required Python packages are not installed."
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# Print banner
echo "====================================="
echo "     SCRIPT BUDGET ANALYZER         "
echo "====================================="
echo ""

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: ./script_budget.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -f, --file FILE     Path to script file (text or PDF)"
    echo "  -b, --budget LEVEL  Budget level (low, medium, high) [default: low]"
    echo "  -o, --output FILE   Output file for the budget [default: print to console]"
    echo "  -h, --help          Show this help message"
    echo ""
    exit 0
fi

# Parse arguments
FILE=""
BUDGET="low"
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--file)
            FILE="$2"
            shift 2
            ;;
        -b|--budget)
            BUDGET="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# Check if file is provided
if [ -z "$FILE" ]; then
    echo "No script file provided. Please specify a file with -f option."
    echo "Use --help for usage information."
    exit 1
fi

# Check if file exists
if [ ! -f "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

# Check if budget level is valid
if [[ "$BUDGET" != "low" && "$BUDGET" != "medium" && "$BUDGET" != "high" ]]; then
    echo "Invalid budget level: $BUDGET"
    echo "Valid options are: low, medium, high"
    exit 1
fi

# Build command
CMD="python pdf_script_analyzer.py -f \"$FILE\" -b \"$BUDGET\""
if [ ! -z "$OUTPUT" ]; then
    CMD="$CMD -o \"$OUTPUT\""
fi

# Run the command
echo "Analyzing script: $FILE"
echo "Budget level: $BUDGET"
if [ ! -z "$OUTPUT" ]; then
    echo "Output file: $OUTPUT"
fi
echo ""
echo "Running analysis..."
echo ""

# Execute the command
eval $CMD

# Done
echo ""
echo "Analysis complete!" 