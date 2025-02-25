#!/usr/bin/env python3
import argparse
import os
import sys
from script_budget import script_to_budget, process_script_file


def main():
    parser = argparse.ArgumentParser(description='Convert a film script into a production budget')
    parser.add_argument('--file', '-f', type=str, help='Path to script file (text or PDF)')
    parser.add_argument('--budget', '-b', type=str, choices=['low', 'medium', 'high'],
                        default='low', help='Budget level (default: low)')
    parser.add_argument('--output', '-o', type=str, help='Output file for the budget (default: print to console)')

    args = parser.parse_args()

    # Handle script input
    script_content = ""
    if args.file:
        try:
            # Use the process_script_file function that handles both text and PDF files
            print(f"\nProcessing script file: {args.file}")
            print(f"Budget level: {args.budget}")
            print("This may take a few minutes depending on the script length.\n")
            
            # Process the file and get the result
            result = process_script_file(args.file, args.budget)
            
            # Output the results
            if args.output:
                with open(args.output, 'w') as f:
                    f.write("===== SCRIPT ANALYSIS =====\n\n")
                    f.write(result["script_analysis"])
                    f.write("\n\n===== PRODUCTION BUDGET =====\n\n")
                    f.write(result["budget"])
                    f.write("\n\n===== COST-SAVING SUGGESTIONS =====\n\n")
                    f.write(result["cost_saving_suggestions"])
                print(f"Budget saved to {args.output}")
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
    print(f"\nProcessing script with {args.budget} budget level...")
    print("This may take a few minutes depending on the script length.\n")

    result = script_to_budget(script_content, args.budget)

    # Output the results
    if args.output:
        with open(args.output, 'w') as f:
            f.write("===== SCRIPT ANALYSIS =====\n\n")
            f.write(result["script_analysis"])
            f.write("\n\n===== PRODUCTION BUDGET =====\n\n")
            f.write(result["budget"])
            f.write("\n\n===== COST-SAVING SUGGESTIONS =====\n\n")
            f.write(result["cost_saving_suggestions"])
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