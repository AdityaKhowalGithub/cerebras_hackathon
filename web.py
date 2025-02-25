from flask import Flask, render_template, request, jsonify
from pdf_script_analyzer import extract_text_from_pdf, process_script, process_script_file
import os
import tempfile
import markdown2
import re

app = Flask(__name__)


def format_budget_as_table(budget_text):
    """Convert budget text to HTML table format"""
    # Use markdown2 to convert the markdown (including tables) to HTML
    # The 'tables' extra ensures proper table parsing
    html = markdown2.markdown(budget_text, extras=["tables", "fenced-code-blocks"])
    
    # Wrap the result in a div with class for styling
    html = f"<div class='budget-table'>{html}</div>"
    
    return html


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_script', methods=['POST'])
def process_script_route():
    # Check if budget level is provided
    budget_level = request.form.get('budget_level', 'low') if request.form else request.json.get('budget_level', 'low')
    
    if 'script_file' in request.files and request.files['script_file'].filename:
        # Handle file upload
        script_file = request.files['script_file']
        file_ext = os.path.splitext(script_file.filename)[1].lower()
        
        # Create a temporary file to save the uploaded file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        script_file.save(temp_file.name)
        temp_file.close()
        
        try:
            # Process the file using our standalone function
            result = process_script_file(temp_file.name, budget_level)
            
            # Remove the temporary file
            os.unlink(temp_file.name)
            
            # Convert markdown to HTML
            result['script_analysis_html'] = markdown2.markdown(result['script_analysis'])
            result['budget_html'] = format_budget_as_table(result['budget'])
            result['cost_saving_suggestions_html'] = markdown2.markdown(result['cost_saving_suggestions'])
            
            return jsonify(result)
        except Exception as e:
            # Clean up the temporary file if there was an error
            os.unlink(temp_file.name)
            return jsonify({'error': str(e)}), 500
    else:
        # Get script content from form data or JSON
        if request.form:
            script_content = request.form.get('script', '')
        else:
            script_content = request.json.get('script', '')
    
        if not script_content.strip():
            return jsonify({'error': 'No script content provided'}), 400

        try:
            # Process the script using our standalone function
            result = process_script(script_content, budget_level)
            
            # Convert markdown to HTML
            result['script_analysis_html'] = markdown2.markdown(result['script_analysis'])
            result['budget_html'] = format_budget_as_table(result['budget'])
            result['cost_saving_suggestions_html'] = markdown2.markdown(result['cost_saving_suggestions'])
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# Make sure the templates directory exists
os.makedirs('templates', exist_ok=True)

if __name__ == '__main__':
    # Check if CEREBRAS_API_KEY is set
    if not os.environ.get('CEREBRAS_API_KEY'):
        print("Warning: CEREBRAS_API_KEY environment variable is not set.")
        print("Please set it before running the application:")
        print("export CEREBRAS_API_KEY=\"your-api-key-here\"")
        # We've set it in the pdf_script_analyzer.py already, so we're good

    print("Starting web server... Open http://127.0.0.1:8080 in your browser")
    app.run(debug=True, port=8080)