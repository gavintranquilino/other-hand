from flask import Flask, render_template, jsonify, request
import os
import json
import re

app = Flask(__name__)

# Configuration
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
LAYOUT_FILE = os.path.join(os.path.dirname(__file__), 'layout.json')

def parse_script_metadata(file_path):
    """Parse name, description, and icon from script docstring"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract docstring
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if not docstring_match:
            return None, None, None
        
        docstring = docstring_match.group(1).strip()
        
        # Parse name and description
        name_match = re.search(r'Name:\s*(.+)', docstring)
        desc_match = re.search(r'Description:\s*(.+)', docstring)
        icon_match = re.search(r'Icon:\s*(.+)', docstring)
        
        name = name_match.group(1).strip() if name_match else os.path.basename(file_path).replace('.py', '')
        description = desc_match.group(1).strip() if desc_match else "No description available"
        icon = icon_match.group(1).strip() if icon_match else "🔧"
        
        return name, description, icon
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None, None, None

def get_script_code(file_path):
    """Read the full script code"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/scripts')
def get_scripts():
    """Get all available scripts with metadata"""
    scripts = []
    
    if not os.path.exists(SCRIPTS_DIR):
        os.makedirs(SCRIPTS_DIR)
    
    for filename in os.listdir(SCRIPTS_DIR):
        if filename.endswith('.py'):
            file_path = os.path.join(SCRIPTS_DIR, filename)
            name, description, icon = parse_script_metadata(file_path)
            
            if name:  # Only include if we could parse metadata
                scripts.append({
                    'id': filename.replace('.py', ''),
                    'name': name,
                    'description': description,
                    'icon': icon,
                    'path': filename,
                    'code': get_script_code(file_path)
                })
    
    return jsonify(scripts)

@app.route('/api/layout', methods=['GET'])
def get_layout():
    """Get the current layout"""
    if os.path.exists(LAYOUT_FILE):
        try:
            with open(LAYOUT_FILE, 'r') as f:
                layout = json.load(f)
            return jsonify(layout)
        except Exception as e:
            print(f"Error reading layout: {e}")
    
    # Return empty layout if file doesn't exist
    return jsonify({
        "000": None, "001": None, "010": None, "011": None,
        "100": None, "101": None, "110": None, "111": None
    })

@app.route('/api/layout', methods=['POST'])
def save_layout():
    """Save the current layout"""
    try:
        layout = request.json
        with open(LAYOUT_FILE, 'w') as f:
            json.dump(layout, f, indent=2)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error saving layout: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)