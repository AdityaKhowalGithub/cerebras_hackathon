from flask import Flask, render_template, request, jsonify, Response
from pdf_script_analyzer import extract_text_from_pdf, process_script, process_script_file
import os
import tempfile
import markdown2
import re
import csv
import io

app = Flask(__name__)


def format_budget_as_table(budget_text):
    """Convert budget text to HTML table format"""
    # Use markdown2 to convert the markdown (including tables) to HTML
    # The 'tables' extra ensures proper table parsing
    html = markdown2.markdown(budget_text, extras=["tables", "fenced-code-blocks"])
    
    # Wrap the result in a div with class for styling
    html = f"<div class='budget-table'>{html}</div>"
    
    return html


def parse_budget_to_csv(budget_text):
    """Convert budget markdown text to CSV data"""
    # Parse markdown tables to extract budget data
    lines = budget_text.split('\n')
    categories = []
    items = []
    
    current_category = "Uncategorized"
    
    for line in lines:
        # Find section headings (categories)
        if line.startswith('##'):
            current_category = line.replace('#', '').strip()
            # Remove any amount in parentheses
            current_category = re.sub(r'\(estimated:.*?\)', '', current_category).strip()
        
        # Parse table rows
        elif '|' in line and not line.startswith('|---'):
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) >= 3 and cells[1] and cells[2]:  # Skip header row and make sure we have item and cost
                item = cells[1].strip()
                cost = cells[2].strip()
                
                if item and cost and 'Item' not in item:  # Skip header rows
                    categories.append(current_category)
                    items.append((item, cost))
    
    # Convert to CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Category', 'Item', 'Cost'])
    
    for i, (item, cost) in enumerate(items):
        writer.writerow([categories[i], item, cost])
    
    return output.getvalue()


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


@app.route('/export_budget_csv', methods=['POST'])
def export_budget_csv():
    """Endpoint to export budget as CSV"""
    if request.form:
        budget_text = request.form.get('budget_text', '')
    else:
        budget_text = request.json.get('budget_text', '')
    
    if not budget_text:
        return jsonify({'error': 'No budget data provided'}), 400
    
    csv_data = parse_budget_to_csv(budget_text)
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=production_budget.csv"}
    )


@app.route('/export_resources_csv', methods=['POST'])
def export_resources_csv():
    """Endpoint to export production resources as CSV"""
    if request.form:
        budget_text = request.form.get('budget_text', '')
    else:
        budget_text = request.json.get('budget_text', '')
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Category', 'Item', 'Estimated Cost', 'Vendor', 'Purchase/Hire Link'])
    
    # Define category mappings for better organization
    category_mappings = {
        'pre-production': 'Pre-Production',
        'pre production': 'Pre-Production',
        'production': 'Production',
        'post-production': 'Post-Production',
        'post production': 'Post-Production',
        'camera': 'Camera Equipment',
        'equipment': 'Production Equipment',
        'cast': 'Cast',
        'talent': 'Cast',
        'crew': 'Crew',
        'location': 'Locations',
        'set': 'Set Design',
        'prop': 'Props',
        'costume': 'Costumes',
        'wardrobe': 'Costumes',
        'makeup': 'Hair & Makeup',
        'hair': 'Hair & Makeup',
        'sound': 'Sound Equipment',
        'audio': 'Sound Equipment',
        'light': 'Lighting Equipment',
        'grip': 'Grip Equipment',
        'electric': 'Electrical Equipment',
        'special effect': 'Special Effects',
        'visual effect': 'Visual Effects',
        'vfx': 'Visual Effects',
        'sfx': 'Special Effects',
        'catering': 'Catering & Craft Services',
        'food': 'Catering & Craft Services',
        'transport': 'Transportation',
        'travel': 'Transportation',
        'insurance': 'Insurance & Legal',
        'legal': 'Insurance & Legal',
        'contingency': 'Contingency'
    }
    
    # Define vendor mappings by category
    vendor_mappings = {
        'Camera Equipment': ('ShareGrid', 'https://sharegrid.com/search?q='),
        'Production Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Lighting Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Grip Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Electrical Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Sound Equipment': ('Sweetwater', 'https://www.sweetwater.com/store/search.php?s='),
        'Props': ('PropHouse', 'https://www.prophouse.com/search?q='),
        'Costumes': ('CostumeSuperCenter', 'https://www.costumesupercenter.com/search?q='),
        'Hair & Makeup': ('MakeupArtistChoice', 'https://www.makeupartistschoice.com/search?q='),
        'Set Design': ('RoseBrand', 'https://www.rosebrand.com/search?q='),
        'Visual Effects': ('VideoHive', 'https://videohive.net/search?q='),
        'Special Effects': ('FXWarehouse', 'https://fxwarehouse.com/search?q='),
        'Cast': ('BackstageHub', 'https://www.backstagehub.com/search?query='),
        'Crew': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Locations': ('StudioList', 'https://www.studiolist.com/search?q='),
        'Transportation': ('BudgetTruck', 'https://www.budgettruck.com/locations?q='),
        'Catering & Craft Services': ('CraftServiceDirect', 'https://www.craftservicesdirect.com/search?q='),
        'Insurance & Legal': ('InsuranceCanopy', 'https://www.insurancecanopy.com/'),
        'Pre-Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Post-Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Contingency': ('ProductionHub', 'https://www.productionhub.com/')
    }
    
    # Add general production resource links
    general_resources = [
        ('Props & Equipment', 'FilmTools - Film Equipment', 'https://www.filmtools.com/'),
        ('Camera Equipment', 'ShareGrid - Camera Rentals', 'https://sharegrid.com/'),
        ('Crew & Talent', 'ProductionHub - Film Professionals', 'https://www.productionhub.com/'),
        ('Locations', 'StudioList - Film Locations', 'https://www.studiolist.com/'),
        ('Cast', 'BackstageHub - Actor Casting', 'https://www.backstagehub.com/'),
        ('Sound Equipment', 'Sweetwater - Audio Equipment', 'https://www.sweetwater.com/'),
        ('Post-Production', 'EditStock - Post-Production', 'https://editstock.com/'),
        ('Insurance', 'InsuranceCanopy - Film Insurance', 'https://www.insurancecanopy.com/'),
        ('Costumes', 'CostumeSuperCenter - Wardrobe', 'https://www.costumesupercenter.com/'),
        ('Special Effects', 'FXWarehouse - SFX Supplies', 'https://fxwarehouse.com/')
    ]
    
    # Add general resources to CSV
    for category, item, url in general_resources:
        writer.writerow([category, 'General Resource', '', item, url])
    
    # If budget data is provided, extract items and add relevant vendor links
    if budget_text:
        # Parse markdown tables to extract budget data
        lines = budget_text.split('\n')
        current_category = "Uncategorized"
        
        for line in lines:
            # Find section headings (categories)
            if line.startswith('##'):
                current_category = line.replace('#', '').strip()
                # Remove any amount in parentheses
                current_category = re.sub(r'\(estimated:.*?\)', '', current_category).strip()
            
            # Parse table rows
            elif '|' in line and not line.startswith('|---'):
                cells = [cell.strip() for cell in line.split('|')]
                if len(cells) >= 3 and cells[1] and cells[2]:  # Make sure we have item and cost
                    item = cells[1].strip()
                    cost = cells[2].strip()
                    
                    if item and cost and 'Item' not in item:  # Skip header rows
                        # Special handling for props items
                        if 'prop' in item.lower() or 'prop' in current_category.lower():
                            # Force the category to be "Props" for anything prop-related
                            matched_category = "Props"
                            
                            # Check if it's a compound prop item that needs to be split
                            # Look for patterns like "Special Props (Item1, Item2)" or similar
                            prop_items = []
                            
                            # Check for props list in parentheses
                            parentheses_match = re.search(r'\((.*?)\)', item)
                            if parentheses_match:
                                # Get the base prop name (before the parentheses)
                                base_prop_name = item.split('(')[0].strip()
                                
                                # Get the items inside parentheses and split by commas
                                items_in_parentheses = parentheses_match.group(1)
                                split_items = [i.strip() for i in re.split(r',|;|and', items_in_parentheses)]
                                
                                # If there are multiple items and 'etc' is not the only one
                                if len(split_items) > 1 or not any(x.lower() in ['etc', 'etc.', 'and so on', 'and more'] for x in split_items):
                                    for prop_item in split_items:
                                        if prop_item.lower() not in ['etc', 'etc.', 'and so on', 'and more']:
                                            # Create a clean name for the individual prop
                                            clean_prop_name = prop_item.strip()
                                            prop_items.append(clean_prop_name)
                            
                            # If we successfully split the compound prop item
                            if prop_items:
                                # Add each prop as a separate item
                                for prop_item in prop_items:
                                    # Find the appropriate vendor
                                    vendor_name, vendor_base_url = vendor_mappings.get('Props', ('PropHouse', 'https://www.prophouse.com/search?q='))
                                    
                                    # Create the vendor URL
                                    search_query = re.sub(r'[^\w\s]', ' ', prop_item).strip()
                                    vendor_url = vendor_base_url + search_query.replace(' ', '+')
                                    
                                    # Write to CSV
                                    writer.writerow([matched_category, prop_item, cost, vendor_name, vendor_url])
                                
                                # Skip the default item adding logic below since we've already added the split items
                                continue
                        else:
                            # Determine the best category for this item
                            matched_category = current_category
                            
                            # Try to find a better category match based on the item or current category
                            for keyword, mapped_category in category_mappings.items():
                                if keyword in item.lower() or keyword in current_category.lower():
                                    matched_category = mapped_category
                                    break
                        
                        # Find the appropriate vendor for this category
                        vendor_name = "ProductionHub"
                        vendor_base_url = "https://www.productionhub.com/directory?q="
                        
                        if matched_category in vendor_mappings:
                            vendor_name, vendor_base_url = vendor_mappings[matched_category]
                        
                        # Create the vendor URL with the item as search query
                        search_query = re.sub(r'[^\w\s]', ' ', item).strip()  # Clean up item for URL
                        vendor_url = vendor_base_url + search_query.replace(' ', '+')
                        
                        # Write to CSV
                        writer.writerow([matched_category, item, cost, vendor_name, vendor_url])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=production_resources.csv"}
    )


@app.route('/get_shopping_links', methods=['POST'])
def get_shopping_links():
    """Endpoint to get shopping links for individual items"""
    if request.form:
        data = request.form
    else:
        data = request.json
    
    category = data.get('category', '')
    item = data.get('item', '')
    
    if not category or not item:
        return jsonify({'error': 'Category and item are required'}), 400
    
    # Define vendor mappings by category (same as in export_resources_csv)
    vendor_mappings = {
        'Camera Equipment': ('ShareGrid', 'https://sharegrid.com/search?q='),
        'Production Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Lighting Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Grip Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Electrical Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Sound Equipment': ('Sweetwater', 'https://www.sweetwater.com/store/search.php?s='),
        'Props': ('PropHouse', 'https://www.prophouse.com/search?q='),
        'Costumes': ('CostumeSuperCenter', 'https://www.costumesupercenter.com/search?q='),
        'Hair & Makeup': ('MakeupArtistChoice', 'https://www.makeupartistschoice.com/search?q='),
        'Set Design': ('RoseBrand', 'https://www.rosebrand.com/search?q='),
        'Visual Effects': ('VideoHive', 'https://videohive.net/search?q='),
        'Special Effects': ('FXWarehouse', 'https://fxwarehouse.com/search?q='),
        'Cast': ('BackstageHub', 'https://www.backstagehub.com/search?query='),
        'Crew': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Locations': ('StudioList', 'https://www.studiolist.com/search?q='),
        'Transportation': ('BudgetTruck', 'https://www.budgettruck.com/locations?q='),
        'Catering & Craft Services': ('CraftServiceDirect', 'https://www.craftservicesdirect.com/search?q='),
        'Insurance & Legal': ('InsuranceCanopy', 'https://www.insurancecanopy.com/'),
        'Pre-Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Post-Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Contingency': ('ProductionHub', 'https://www.productionhub.com/')
    }
    
    # Find the appropriate vendor for this category
    vendor_name = "ProductionHub"
    vendor_base_url = "https://www.productionhub.com/directory?q="
    
    if category in vendor_mappings:
        vendor_name, vendor_base_url = vendor_mappings[category]
    
    # Create the vendor URL with the item as search query
    search_query = re.sub(r'[^\w\s]', ' ', item).strip()  # Clean up item for URL
    vendor_url = vendor_base_url + search_query.replace(' ', '+')
    
    result = {
        'category': category,
        'item': item,
        'vendor': vendor_name,
        'url': vendor_url
    }
    
    return jsonify(result)


@app.route('/get_shopping_table_data', methods=['POST'])
def get_shopping_table_data():
    """Endpoint to get data for the shopping links table"""
    if request.form:
        budget_text = request.form.get('budget_text', '')
    else:
        budget_text = request.json.get('budget_text', '')
    
    if not budget_text:
        return jsonify({'error': 'No budget data provided'}), 400
    
    # Define category mappings for better organization (same as in export_resources_csv)
    category_mappings = {
        'pre-production': 'Pre-Production',
        'pre production': 'Pre-Production',
        'production': 'Production',
        'post-production': 'Post-Production',
        'post production': 'Post-Production',
        'camera': 'Camera Equipment',
        'equipment': 'Production Equipment',
        'cast': 'Cast',
        'talent': 'Cast',
        'crew': 'Crew',
        'location': 'Locations',
        'set': 'Set Design',
        'prop': 'Props',
        'costume': 'Costumes',
        'wardrobe': 'Costumes',
        'makeup': 'Hair & Makeup',
        'hair': 'Hair & Makeup',
        'sound': 'Sound Equipment',
        'audio': 'Sound Equipment',
        'light': 'Lighting Equipment',
        'grip': 'Grip Equipment',
        'electric': 'Electrical Equipment',
        'special effect': 'Special Effects',
        'visual effect': 'Visual Effects',
        'vfx': 'Visual Effects',
        'sfx': 'Special Effects',
        'catering': 'Catering & Craft Services',
        'food': 'Catering & Craft Services',
        'transport': 'Transportation',
        'travel': 'Transportation',
        'insurance': 'Insurance & Legal',
        'legal': 'Insurance & Legal',
        'contingency': 'Contingency'
    }
    
    # Define vendor mappings by category (same as above)
    vendor_mappings = {
        'Camera Equipment': ('ShareGrid', 'https://sharegrid.com/search?q='),
        'Production Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Lighting Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Grip Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Electrical Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Sound Equipment': ('Sweetwater', 'https://www.sweetwater.com/store/search.php?s='),
        'Props': ('PropHouse', 'https://www.prophouse.com/search?q='),
        'Costumes': ('CostumeSuperCenter', 'https://www.costumesupercenter.com/search?q='),
        'Hair & Makeup': ('MakeupArtistChoice', 'https://www.makeupartistschoice.com/search?q='),
        'Set Design': ('RoseBrand', 'https://www.rosebrand.com/search?q='),
        'Visual Effects': ('VideoHive', 'https://videohive.net/search?q='),
        'Special Effects': ('FXWarehouse', 'https://fxwarehouse.com/search?q='),
        'Cast': ('BackstageHub', 'https://www.backstagehub.com/search?query='),
        'Crew': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Locations': ('StudioList', 'https://www.studiolist.com/search?q='),
        'Transportation': ('BudgetTruck', 'https://www.budgettruck.com/locations?q='),
        'Catering & Craft Services': ('CraftServiceDirect', 'https://www.craftservicesdirect.com/search?q='),
        'Insurance & Legal': ('InsuranceCanopy', 'https://www.insurancecanopy.com/'),
        'Pre-Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Post-Production': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Contingency': ('ProductionHub', 'https://www.productionhub.com/')
    }
    
    table_data = []
    
    # Parse markdown tables to extract budget data
    lines = budget_text.split('\n')
    current_category = "Uncategorized"
    
    for line in lines:
        # Find section headings (categories)
        if line.startswith('##'):
            current_category = line.replace('#', '').strip()
            # Remove any amount in parentheses
            current_category = re.sub(r'\(estimated:.*?\)', '', current_category).strip()
        
        # Parse table rows
        elif '|' in line and not line.startswith('|---'):
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) >= 3 and cells[1] and cells[2]:  # Make sure we have item and cost
                item = cells[1].strip()
                cost = cells[2].strip()
                
                if item and cost and 'Item' not in item:  # Skip header rows
                    # Special handling for props items
                    if 'prop' in item.lower() or 'prop' in current_category.lower():
                        # Force the category to be "Props" for anything prop-related
                        matched_category = "Props"
                        
                        # Check if it's a compound prop item that needs to be split
                        # Look for patterns like "Special Props (Item1, Item2)" or similar
                        prop_items = []
                        
                        # Check for props list in parentheses
                        parentheses_match = re.search(r'\((.*?)\)', item)
                        if parentheses_match:
                            # Get the base prop name (before the parentheses)
                            base_prop_name = item.split('(')[0].strip()
                            
                            # Get the items inside parentheses and split by commas
                            items_in_parentheses = parentheses_match.group(1)
                            split_items = [i.strip() for i in re.split(r',|;|and', items_in_parentheses)]
                            
                            # If there are multiple items and 'etc' is not the only one
                            if len(split_items) > 1 or not any(x.lower() in ['etc', 'etc.', 'and so on', 'and more'] for x in split_items):
                                for prop_item in split_items:
                                    if prop_item.lower() not in ['etc', 'etc.', 'and so on', 'and more']:
                                        # Create a clean name for the individual prop
                                        clean_prop_name = prop_item.strip()
                                        prop_items.append(clean_prop_name)
                        
                        # If we successfully split the compound prop item
                        if prop_items:
                            # Add each prop as a separate item
                            for prop_item in prop_items:
                                # Find the appropriate vendor
                                vendor_name, vendor_base_url = vendor_mappings.get('Props', ('PropHouse', 'https://www.prophouse.com/search?q='))
                                
                                # Create the vendor URL
                                search_query = re.sub(r'[^\w\s]', ' ', prop_item).strip()
                                vendor_url = vendor_base_url + search_query.replace(' ', '+')
                                
                                # Add to table data
                                table_data.append({
                                    'category': matched_category,
                                    'item': prop_item,
                                    'cost': cost,
                                    'vendor': vendor_name,
                                    'url': vendor_url
                                })
                            # Skip the default item adding logic below since we've already added the split items
                            continue
                    else:
                        # Determine the best category for this item
                        matched_category = current_category
                        
                        # Try to find a better category match based on the item or current category
                        for keyword, mapped_category in category_mappings.items():
                            if keyword in item.lower() or keyword in current_category.lower():
                                matched_category = mapped_category
                                break
                    
                    # Find the appropriate vendor for this category
                    vendor_name = "ProductionHub"
                    vendor_base_url = "https://www.productionhub.com/directory?q="
                    
                    if matched_category in vendor_mappings:
                        vendor_name, vendor_base_url = vendor_mappings[matched_category]
                    
                    # Create the vendor URL with the item as search query
                    search_query = re.sub(r'[^\w\s]', ' ', item).strip()  # Clean up item for URL
                    vendor_url = vendor_base_url + search_query.replace(' ', '+')
                    
                    # Add to table data
                    table_data.append({
                        'category': matched_category,
                        'item': item,
                        'cost': cost,
                        'vendor': vendor_name,
                        'url': vendor_url
                    })
    
    return jsonify(table_data)


@app.route('/get_script_specific_items', methods=['POST'])
def get_script_specific_items():
    """Endpoint to get items specifically mentioned in the script analysis with detailed prop extraction"""
    if request.form:
        data = request.form
    else:
        data = request.json
    
    script_analysis = data.get('script_analysis', '')
    
    if not script_analysis:
        return jsonify({'error': 'Script analysis is required'}), 400
    
    # Extract important elements from script analysis
    item_categories = {
        'Props': [],
        'Costumes': [],
        'Locations': [],
        'Set Design': [],
        'Camera Equipment': [],
        'Lighting Equipment': [],
        'Sound Equipment': [],
        'Special Effects': [],
        'Hair & Makeup': [],
        'Cast': [],
        'Crew': []
    }
    
    # More detailed prop subcategories for better vendor matching
    prop_subcategories = {
        'Antiques': [],
        'Furniture': [],
        'Weapons': [],
        'Electronics': [],
        'Tools': [],
        'Vehicles': [],
        'Household': [],
        'Office': [],
        'Medical': [],
        'Books': [],
        'Food': [],
        'Period Pieces': [],
        'SciFi': []
    }
    
    # Words to exclude from props and items (articles, prepositions, common verbs, etc.)
    exclude_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 
                     'with', 'in', 'out', 'of', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should',
                     'may', 'might', 'must', 'can', 'could', 'that', 'this', 'these', 'those'}
    
    # ---------------- MAIN PROP EXTRACTION PATTERNS ----------------
    
    # 1. Try to identify dedicated props section in the analysis
    props_pattern = r'(?:props|prop list|key props|prop requirements|important props|prop needs|prop demands|necessary props|essential props)\s*(?::|include|includes|are|will include|needed|required|consist of|comprising)?\s*((?:[\w\s,.\-\(\)\'\"&+]+(?:,|\.|\n|$))+)'
    props_match = re.search(props_pattern, script_analysis.lower(), re.IGNORECASE)
    
    if props_match:
        props_text = props_match.group(1)
        # Split by commas, periods, or newlines, then clean up
        raw_props = re.split(r'[,.\n]', props_text)
        for prop in raw_props:
            prop = prop.strip()
            if prop and len(prop) > 2 and not all(word in exclude_words for word in prop.lower().split()):
                # Check if the prop item itself contains a list in parentheses
                extract_props_from_text(prop, item_categories, prop_subcategories, exclude_words)
    
    # 2. Look for scene headings with props explicitly mentioned
    scene_prop_pattern = r'(?:INT|EXT|INT\./EXT|EXT\./INT)\.?\s+[^.]*?\s+(?:-|–)\s+[^.]*?(?:with|containing|featuring)\s+((?:[\w\s,.\-\(\)\'\"&+]+))'
    scene_prop_matches = re.finditer(scene_prop_pattern, script_analysis, re.IGNORECASE)
    
    for match in scene_prop_matches:
        props_text = match.group(1).strip()
        extract_props_from_text(props_text, item_categories, prop_subcategories, exclude_words)
    
    # 3. Look for props in character actions and descriptions
    action_patterns = [
        r'(?:holding|carries|carrying|using|wielding|handling|grabs|picks up|puts down|places|sets down|examines|inspects|looks at|operates|activates)\s+(?:a|an|the|some|several|their|his|her)?\s+((?:[\w\s\-\'\"]+(?:\s+(?:of|with|from|by|in|on|that|which|from)\s+[\w\s\-\'\"]+)?))',
        r'(?:takes out|pulls out|removes|extracts|withdraws|retrieves)\s+(?:a|an|the|some|several|their|his|her)?\s+((?:[\w\s\-\'\"]+(?:\s+(?:of|with|from|by|in|on|that|which|from)\s+[\w\s\-\'\"]+)?))',
        r'(?:sits on|stands on|lies on|placed on|resting on|positioned on)\s+(?:a|an|the|some|several|their|his|her)?\s+((?:[\w\s\-\'\"]+(?:\s+(?:of|with|from|by|in|on|that|which|from)\s+[\w\s\-\'\"]+)?))',
        r'(?:equipped with|armed with|furnished with|decorated with|adorned with)\s+(?:a|an|the|some|several|their|his|her)?\s+((?:[\w\s\-\'\"]+(?:\s+(?:of|with|from|by|in|on|that|which|from)\s+[\w\s\-\'\"]+)?))',
        r'(?:notable prop|special prop|unique prop|key prop|important prop)s?(?:\s+include|\s+are|\s+is|\:)?\s+((?:[\w\s,.\-\(\)\'\"&+]+))'
    ]
    
    for pattern in action_patterns:
        action_matches = re.finditer(pattern, script_analysis, re.IGNORECASE)
        for match in action_matches:
            potential_prop = match.group(1).strip()
            extract_props_from_text(potential_prop, item_categories, prop_subcategories, exclude_words)
    
    # 4. Look for props in set descriptions
    set_patterns = [
        r'(?:the (?:room|area|space|setting|scene|location|place|interior|exterior) (?:contains|has|features|includes|with|displays))\s+((?:[\w\s,.\-\(\)\'\"&+]+))',
        r'(?:the (?:set|scene|location) (?:is decorated with|is furnished with|requires|needs|should have|must have|displays))\s+((?:[\w\s,.\-\(\)\'\"&+]+))',
        r'(?:on the (?:table|desk|shelf|counter|wall|floor|ceiling|bed|chair|sofa|couch))\s+((?:[\w\s,.\-\(\)\'\"&+]+))',
        r'(?:set (?:decoration|design|dressing|pieces|elements|items|props))\s+(?:include|includes|are|consist of|comprising|:)?\s+((?:[\w\s,.\-\(\)\'\"&+]+))'
    ]
    
    for pattern in set_patterns:
        set_matches = re.finditer(pattern, script_analysis, re.IGNORECASE)
        for match in set_matches:
            potential_props = match.group(1).strip()
            extract_props_from_text(potential_props, item_categories, prop_subcategories, exclude_words)
    
    # 5. Extract period-specific props if mentioned
    period_matches = re.search(r'(?:set in|takes place in|during|era|period of|time period|historical period)(?:\s+the)?\s+([\w\s\-\'\"]+(?:century|s|era|period|dynasty|ages|ages))', script_analysis, re.IGNORECASE)
    
    period_settings = []
    if period_matches:
        period = period_matches.group(1).strip()
        period_settings.append(period)
        
        # Add period-specific props based on the era
        add_period_specific_props(period, prop_subcategories)
    
    # 6. Process script for specialized prop categories (like weapons, vehicles, tech)
    specialized_patterns = {
        'Weapons': r'(?:gun|rifle|pistol|sword|knife|dagger|axe|bow|arrow|shield|armor|weapon|firearm|blade|shotgun|revolver|grenade|explosive|bomb)',
        'Electronics': r'(?:computer|laptop|phone|smartphone|tablet|tv|television|radio|device|gadget|camera|microphone|headphones|speaker|screen|monitor|console|robot)',
        'Vehicles': r'(?:car|truck|van|motorcycle|bike|bicycle|bus|train|plane|aircraft|boat|ship|vessel|submarine|helicopter|spaceship|wagon|cart)',
        'Furniture': r'(?:table|chair|desk|sofa|couch|bed|cabinet|wardrobe|dresser|bookshelf|shelf|bench|stool|ottoman|armchair|recliner)',
        'Antiques': r'(?:antique|vintage|historical|ancient|old-fashioned|heirloom|classic|period|relic|artifact)'
    }
    
    for category, pattern in specialized_patterns.items():
        specialized_matches = re.finditer(pattern, script_analysis, re.IGNORECASE)
        for match in specialized_matches:
            # Extract the full phrase containing the specialized prop (up to 6 words before and after)
            start = max(0, match.start() - 40)
            end = min(len(script_analysis), match.end() + 40)
            context = script_analysis[start:end]
            
            # Find the specialized item with potential descriptors
            context_words = context.split()
            if len(context_words) > 2:
                middle_index = len(context_words) // 2
                # Look for patterns like "adjective + specialized item + potential descriptor"
                for i in range(max(0, middle_index - 3), min(len(context_words) - 1, middle_index + 3)):
                    if re.search(pattern, context_words[i], re.IGNORECASE):
                        # Try to capture descriptors (2-3 words before and after)
                        start_idx = max(0, i - 2)
                        end_idx = min(len(context_words), i + 3)
                        prop_phrase = " ".join(context_words[start_idx:end_idx])
                        
                        # Clean up the phrase
                        prop_phrase = re.sub(r'[^\w\s\-\'\"]+', ' ', prop_phrase)
                        prop_phrase = prop_phrase.strip()
                        
                        if prop_phrase and not all(word in exclude_words for word in prop_phrase.lower().split()):
                            prop_subcategories[category].append(prop_phrase)
    
    # Helper function to extract props from text segments
    def extract_props_from_text(text, categories, subcategories, exclude_list):
        # Check if it contains multiple items in parentheses
        parentheses_match = re.search(r'\((.*?)\)', text)
        if parentheses_match:
            # Get the base name (before the parentheses)
            base_name = text.split('(')[0].strip()
            
            # Get items inside parentheses and split by commas, semicolons, 'and', or 'or'
            items_inside = parentheses_match.group(1)
            split_items = [i.strip() for i in re.split(r',|;|\s+and\s+|\s+or\s+', items_inside)]
            
            # Filter out "etc" and similar non-specific items
            non_specific = ['etc', 'etc.', 'and so on', 'and more', 'similar items', 'among others']
            has_specific_items = not all(any(ns in item.lower() for ns in non_specific) for item in split_items)
            
            if has_specific_items:
                for item in split_items:
                    # Skip non-specific terms
                    if not any(ns in item.lower() for ns in non_specific) and len(item) > 2:
                        # If base name gives context, include it
                        clean_item = item.strip()
                        if not base_name.lower() in ['props', 'items', 'equipment', 'objects', 'things']:
                            # Combine base name for context if it's meaningful
                            if not any(clean_item.lower() in existing.lower() for existing in categories['Props']):
                                # Add the specific item
                                categories['Props'].append(clean_item)
                                
                                # Categorize into subcategories
                                categorize_prop(clean_item, subcategories)
                else:
                            # Add just the item if base name is generic
                            if not any(clean_item.lower() in existing.lower() for existing in categories['Props']):
                                categories['Props'].append(clean_item)
                                
                                # Categorize into subcategories
                                categorize_prop(clean_item, subcategories)
            else:
                # If no specific items, add the whole text minus parenthetical if it's meaningful
                clean_text = re.sub(r'\([^)]*\)', '', text).strip()
                if clean_text and len(clean_text) > 2 and not all(word in exclude_list for word in clean_text.lower().split()):
                    if not any(clean_text.lower() in existing.lower() for existing in categories['Props']):
                        categories['Props'].append(clean_text)
                        
                        # Categorize into subcategories
                        categorize_prop(clean_text, subcategories)
        else:
            # For non-parenthetical text, check if it's comma-separated
            if ',' in text:
                items = [item.strip() for item in text.split(',')]
                for item in items:
                    if item and len(item) > 2 and not all(word in exclude_list for word in item.lower().split()):
                        if not any(item.lower() in existing.lower() for existing in categories['Props']):
                            categories['Props'].append(item)
                            
                            # Categorize into subcategories
                            categorize_prop(item, subcategories)
            else:
                # Clean up and add single item
                clean_text = re.sub(r'[^\w\s\-\'\"]+', ' ', text).strip()
                if clean_text and len(clean_text) > 2 and not all(word in exclude_list for word in clean_text.lower().split()):
                    words = clean_text.split()
                    # If too many words, try to extract just the main noun phrase (3-5 words max)
                    if len(words) > 5:
                        # Keep first 4-5 meaningful words
                        meaningful_words = [word for word in words[:8] if word.lower() not in exclude_list]
                        clean_text = ' '.join(meaningful_words[:5])
                    
                    if not any(clean_text.lower() in existing.lower() for existing in categories['Props']):
                        categories['Props'].append(clean_text)
                        
                        # Categorize into subcategories
                        categorize_prop(clean_text, subcategories)
    
    # Helper function to categorize props into subcategories
    def categorize_prop(prop, subcategories):
        prop_lower = prop.lower()
        
        # Dictionary of subcategory patterns
        subcategory_patterns = {
            'Antiques': ['antique', 'vintage', 'ancient', 'historical', 'classic', 'period', 'relic', 'artifact', 'old-fashioned', 'traditional'],
            'Furniture': ['table', 'chair', 'desk', 'sofa', 'couch', 'bed', 'cabinet', 'wardrobe', 'dresser', 'shelf', 'bookshelf', 'drawer', 'bench', 'stool'],
            'Weapons': ['gun', 'rifle', 'pistol', 'sword', 'knife', 'dagger', 'axe', 'bow', 'arrow', 'shield', 'weapon', 'firearm', 'blade', 'shotgun', 'revolver'],
            'Electronics': ['computer', 'laptop', 'phone', 'smartphone', 'tablet', 'tv', 'television', 'radio', 'device', 'camera', 'microphone', 'electronic'],
            'Tools': ['hammer', 'screwdriver', 'drill', 'saw', 'wrench', 'pliers', 'tool', 'equipment', 'device', 'utility', 'mechanical'],
            'Vehicles': ['car', 'truck', 'van', 'motorcycle', 'bike', 'bicycle', 'bus', 'train', 'plane', 'aircraft', 'boat', 'ship', 'vessel', 'vehicle'],
            'Household': ['lamp', 'cup', 'glass', 'plate', 'bowl', 'utensil', 'fork', 'knife', 'spoon', 'pot', 'pan', 'kettle', 'appliance', 'domestic'],
            'Office': ['pen', 'pencil', 'paper', 'document', 'file', 'folder', 'binder', 'stapler', 'clip', 'paperweight', 'business', 'stationery'],
            'Medical': ['syringe', 'bandage', 'prescription', 'medicine', 'pill', 'vaccine', 'medical', 'hospital', 'health', 'clinical', 'stethoscope'],
            'Books': ['book', 'novel', 'journal', 'diary', 'notebook', 'magazine', 'newspaper', 'publication', 'literature', 'reading'],
            'Food': ['food', 'drink', 'beverage', 'meal', 'snack', 'fruit', 'vegetable', 'meat', 'dessert', 'cuisine', 'dish', 'culinary'],
            'SciFi': ['robot', 'alien', 'futuristic', 'space', 'laser', 'hologram', 'gadget', 'sci-fi', 'technological', 'advanced']
        }
        
        matched = False
        for subcategory, keywords in subcategory_patterns.items():
            if any(keyword in prop_lower for keyword in keywords):
                if not any(prop.lower() in existing.lower() for existing in subcategories[subcategory]):
                    subcategories[subcategory].append(prop)
                    matched = True
        
        # If no subcategory matched, add to the appropriate decade/period if it matches
        if not matched:
            for period_subcategory in ['Period Pieces']:
                if not any(prop.lower() in existing.lower() for existing in subcategories[period_subcategory]):
                    subcategories[period_subcategory].append(prop)
    
    # Helper function to add period-specific props based on identified era
    def add_period_specific_props(period, subcategories):
        period_lower = period.lower()
        
        # Dictionary mapping periods to typical props
        period_props = {
            '1920': ['flapper dress', 'feather headband', 'art deco lamp', 'gramophone', 'pocket watch', 'typewriter', 'fedora hat'],
            '1930': ['depression era furniture', 'bakelite radio', 'mechanical typewriter', 'film noir hat', 'vintage microphone'],
            '1940': ['WWII memorabilia', 'ration booklets', 'victory garden tools', 'swing era records', 'vintage camera'],
            '1950': ['poodle skirt', 'jukebox', 'vinyl records', 'drive-in movie speaker', 'rotary phone', 'TV dinner tray'],
            '1960': ['lava lamp', 'peace sign necklace', 'tie-dye shirt', 'record player', 'vintage guitar', 'mod dress'],
            '1970': ['disco ball', 'platform shoes', 'macramé wall hanging', 'bean bag chair', '8-track player', 'mood ring'],
            '1980': ['walkman', 'boombox', 'rubik\'s cube', 'arcade game', 'neon accessories', 'polaroid camera'],
            '1990': ['slap bracelet', 'discman', 'tamagotchi', 'pager', 'dial-up modem', 'cassette tape'],
            'victorian': ['top hat', 'corset', 'pocket watch', 'parasol', 'writing desk', 'oil lamp', 'fainting couch'],
            'medieval': ['sword', 'shield', 'goblet', 'wooden tankard', 'scroll', 'horse saddle', 'bow and arrow'],
            'future': ['holographic display', 'neural interface', 'energy weapon', 'hover vehicle', 'smart fabric clothing']
        }
        
        # Add period-specific props based on matched keywords
        for period_key, props in period_props.items():
            if period_key in period_lower or (period_key.isdigit() and period_key in period_lower):
                for prop in props:
                    if not any(prop.lower() in existing.lower() for existing in subcategories['Period Pieces']):
                        subcategories['Period Pieces'].append(prop)
    
    # Consolidate props from subcategories back to main props list
    for subcategory, props in prop_subcategories.items():
        for prop in props:
            if not any(prop.lower() in existing.lower() for existing in item_categories['Props']):
                item_categories['Props'].append(prop)
    
    # Define specialized vendor mappings based on prop types
    specialized_vendor_mappings = {
        'Antiques': [
            ('Etsy Vintage', 'https://www.etsy.com/search?q=vintage+'),
            ('Ruby Lane', 'https://www.rubylane.com/search?q='),
            ('1stDibs', 'https://www.1stdibs.com/search/?q=')
        ],
        'Furniture': [
            ('Wayfair', 'https://www.wayfair.com/keyword.php?keyword='),
            ('Ikea', 'https://www.ikea.com/us/en/search/?q='),
            ('Restoration Hardware', 'https://rh.com/catalog/search.jsp?query=')
        ],
        'Weapons': [
            ('The Prop House', 'https://prophouse.com/search?q=prop+'),
            ('The Specialists LTD', 'https://www.theprophouse.com/browse/weapons?keywords='),
            ('Modern Props', 'https://modernprops.com/category/?q=')
        ],
        'Electronics': [
            ('B&H Photo Video', 'https://www.bhphotovideo.com/c/search?q='),
            ('Adorama', 'https://www.adorama.com/l/?searchinfo='),
            ('Best Buy', 'https://www.bestbuy.com/site/searchpage.jsp?st=')
        ],
        'Tools': [
            ('Home Depot', 'https://www.homedepot.com/s/'),
            ('Lowe\'s', 'https://www.lowes.com/search?searchTerm='),
            ('Harbor Freight', 'https://www.harborfreight.com/search?q=')
        ],
        'Vehicles': [
            ('Picture Car Warehouse', 'http://www.picturecarwarehouse.com/'),
            ('Cinema Vehicles', 'https://cinemavehicles.com/vehicles/?search='),
            ('Movie Cars Central', 'https://www.moviecarscentral.com/search?q=')
        ],
        'Household': [
            ('Bed Bath & Beyond', 'https://www.bedbathandbeyond.com/store/s/'),
            ('Williams Sonoma', 'https://www.williams-sonoma.com/search/results.html?words='),
            ('Target', 'https://www.target.com/s?searchTerm=')
        ],
        'Office': [
            ('Staples', 'https://www.staples.com/'),
            ('Office Depot', 'https://www.officedepot.com/catalog/search.do?Ntt='),
            ('Amazon Office', 'https://www.amazon.com/s?k=office+')
        ],
        'Medical': [
            ('Medical Props', 'https://www.medicalprops.com/search?q='),
            ('Anatomical Chart Company', 'https://www.anatomycharts.com/search?q='),
            ('Amazon Medical', 'https://www.amazon.com/s?k=medical+')
        ],
        'Books': [
            ('AbeBooks', 'https://www.abebooks.com/servlet/SearchResults?kn='),
            ('Thriftbooks', 'https://www.thriftbooks.com/browse/?b.search='),
            ('Amazon Books', 'https://www.amazon.com/s?k=book+')
        ],
        'Food': [
            ('Fake Food', 'https://www.fakefood.com/search?q='),
            ('Prop Food', 'https://www.propfood.com/collections/all?q='),
            ('Food Styling Props', 'https://www.foodstylingprops.com/search?q=')
        ],
        'Period Pieces': [
            ('Historical Emporium', 'https://www.historicalemporium.com/search/?q='),
            ('Museum Replicas', 'https://www.museumreplicas.com/search?q='),
            ('Vintage Stock Props', 'https://www.vintagestockprops.com/search?q=')
        ],
        'SciFi': [
            ('Weta Workshop', 'https://www.wetanz.com/shop/search?q='),
            ('The Monster Shop', 'https://themonstershop.com/search?q='),
            ('XFXSP', 'https://www.xfxsp.com/search?q=')
        ]
    }
    
    # Main prop vendor mappings (used if no specialized vendor is found)
    general_prop_vendors = [
        ('The Prop House', 'https://www.prophouse.com/search?q='),
        ('eBay', 'https://www.ebay.com/sch/i.html?_nkw='),
        ('Amazon', 'https://www.amazon.com/s?k='),
        ('Etsy', 'https://www.etsy.com/search?q=')
    ]
    
    # General vendor mappings by category
    vendor_mappings = {
        'Camera Equipment': ('ShareGrid', 'https://sharegrid.com/search?q='),
        'Production Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Lighting Equipment': ('FilmTools', 'https://www.filmtools.com/search-results?q='),
        'Sound Equipment': ('Sweetwater', 'https://www.sweetwater.com/store/search.php?s='),
        'Props': ('PropHouse', 'https://www.prophouse.com/search?q='),
        'Costumes': ('CostumeSuperCenter', 'https://www.costumesupercenter.com/search?q='),
        'Hair & Makeup': ('MakeupArtistChoice', 'https://www.makeupartistschoice.com/search?q='),
        'Set Design': ('RoseBrand', 'https://www.rosebrand.com/search?q='),
        'Special Effects': ('FXWarehouse', 'https://fxwarehouse.com/search?q='),
        'Cast': ('BackstageHub', 'https://www.backstagehub.com/search?query='),
        'Crew': ('ProductionHub', 'https://www.productionhub.com/directory?q='),
        'Locations': ('StudioList', 'https://www.studiolist.com/search?q=')
    }
    
    # Build the result with detailed prop information
    result = []
    
    # Helper function to create a more specific search URL
    def create_specific_search_url(prop, vendor_base_url):
        # Remove articles and common words to focus on key terms
        search_terms = []
        
        for word in prop.split():
            if word.lower() not in exclude_words:
                search_terms.append(word)
        
        # Create search query with the most specific terms
        clean_search = " ".join(search_terms)
        clean_search = re.sub(r'[^\w\s]', ' ', clean_search).strip()
        
        # Format search terms for URL
        url_search = clean_search.replace(' ', '+')
        
        # Add quotes for exact matching in some vendors
        if 'amazon.com' in vendor_base_url or 'ebay.com' in vendor_base_url:
            url_search = '%22' + url_search + '%22'
        
        return vendor_base_url + url_search
    
    # Process props and add to result with vendor links
    for category, items in item_categories.items():
        if category == 'Props':  # Special processing for props with subcategories
            processed_props = set()  # Keep track of processed props to avoid duplicates
            
            # First process props from subcategories for more specialized vendors
            for subcategory, subprops in prop_subcategories.items():
                for prop in subprops:
                    # Skip if already processed
                    if prop.lower() in processed_props:
                        continue
                    
                    # Find specialized vendors for this subcategory
                    if subcategory in specialized_vendor_mappings:
                        vendors = specialized_vendor_mappings[subcategory]
                        
                        # Create search URL with specific terms
                        vendor_name, vendor_base_url = vendors[0]  # Use first (primary) vendor
                        vendor_url = create_specific_search_url(prop, vendor_base_url)
                        
                        # Add alternate vendor links
                        alternate_vendors = []
                        if len(vendors) > 1:
                            for alt_vendor_name, alt_vendor_url in vendors[1:]:
                                alternate_vendors.append({
                                    'name': alt_vendor_name,
                                    'url': create_specific_search_url(prop, alt_vendor_url)
                                })
                        
                        result.append({
                            'category': 'Props',
                            'subcategory': subcategory,
                            'item': prop,
                            'cost': 'Varies',
                            'vendor': vendor_name,
                            'url': vendor_url,
                            'alternate_vendors': alternate_vendors,
                            'script_specific': True
                        })
                        
                        processed_props.add(prop.lower())
            
            # Then process remaining general props
            for prop in items:
                if prop.lower() not in processed_props:
                    # Use general prop vendors
                    vendor_name, vendor_base_url = general_prop_vendors[0]
                    vendor_url = create_specific_search_url(prop, vendor_base_url)
                    
                    # Add alternate vendor links
                    alternate_vendors = []
                    for alt_vendor_name, alt_vendor_url in general_prop_vendors[1:]:
                        alternate_vendors.append({
                            'name': alt_vendor_name,
                            'url': create_specific_search_url(prop, alt_vendor_url)
                        })
                    
                    result.append({
                        'category': 'Props',
                        'subcategory': 'General Props',
                        'item': prop,
                        'cost': 'Varies',
                        'vendor': vendor_name,
                        'url': vendor_url,
                        'alternate_vendors': alternate_vendors,
                        'script_specific': True
                    })
                    
                    processed_props.add(prop.lower())
        else:  # Standard processing for non-prop categories
            for item in items:
                # Find the appropriate vendor for this category
                vendor_name = "ProductionHub"
                vendor_base_url = "https://www.productionhub.com/directory?q="
                
                if category in vendor_mappings:
                    vendor_name, vendor_base_url = vendor_mappings[category]
                
                # Create the vendor URL with the item as search query
                vendor_url = create_specific_search_url(item, vendor_base_url)
                
                result.append({
                    'category': category,
                    'item': item,
                    'cost': 'Varies',
                    'vendor': vendor_name,
                    'url': vendor_url,
                    'script_specific': True
                })
    
    return jsonify(result)


# Make sure the templates directory exists
os.makedirs('templates', exist_ok=True)

if __name__ == '__main__':
    # Check if CEREBRAS_API_KEY is set
    if not os.environ.get('CEREBRAS_API_KEY'):
        print("Warning: CEREBRAS_API_KEY environment variable is not set.")
        print("Please set it before running the application:")
        print("export CEREBRAS_API_KEY=\"your-api-key-here\"")
        # We've set it in the pdf_script_analyzer.py already, so we're good

    print("Starting web server... Open http://127.0.0.1:8081 in your browser")
    app.run(debug=True, port=8081)