from flask import Flask, render_template, jsonify, request
import os
import json
import re

app = Flask(__name__)

# Configuration
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
LAYOUT_FILE = os.path.join(os.path.dirname(__file__), 'layout.json')

def parse_script_metadata(file_path):
    """Parse name, description, icon, and color from script docstring"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract docstring
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if not docstring_match:
            return None, None, None, None
        
        docstring = docstring_match.group(1).strip()
        
        # Parse name, description, icon, and color
        name_match = re.search(r'Name:\s*(.+)', docstring)
        desc_match = re.search(r'Description:\s*(.+)', docstring)
        icon_match = re.search(r'Icon:\s*(.+)', docstring)
        color_match = re.search(r'Color:\s*(.+)', docstring)
        
        name = name_match.group(1).strip() if name_match else os.path.basename(file_path).replace('.py', '')
        description = desc_match.group(1).strip() if desc_match else "No description available"
        icon = icon_match.group(1).strip() if icon_match else "🔧"
        color = color_match.group(1).strip() if color_match else None
        
        return name, description, icon, color
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None, None, None, None

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
            name, description, icon, color = parse_script_metadata(file_path)
            
            if name:  # Only include if we could parse metadata
                scripts.append({
                    'id': filename.replace('.py', ''),
                    'name': name,
                    'description': description,
                    'icon': icon,
                    'color': color,
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

@app.route('/api/scripts', methods=['POST'])
def create_script():
    """Create a new script file"""
    try:
        data = request.json
        name = data.get('name', 'Unnamed')
        description = data.get('description', 'No description')
        icon = data.get('icon', '🔧')
        color = data.get('color')
        code = data.get('code', '')
        
        if not name:
            return jsonify({"success": False, "error": "Script name is required"}), 400
        
        # Generate script ID from name
        script_id = name.lower().replace(' ', '_').replace('-', '_')
        # Remove any non-alphanumeric characters except underscore
        import re
        script_id = re.sub(r'[^a-z0-9_]', '', script_id)
        
        if not script_id:
            script_id = 'untitled_script'
        
        # Check if file already exists
        script_path = os.path.join(SCRIPTS_DIR, f"{script_id}.py")
        counter = 1
        original_id = script_id
        while os.path.exists(script_path):
            script_id = f"{original_id}_{counter}"
            script_path = os.path.join(SCRIPTS_DIR, f"{script_id}.py")
            counter += 1
        
        # Create the script content
        color_line = f"Color: {color}\n" if color else ""
        script_content = f'''"""
Name: {name}
Description: {description}
Icon: {icon}
{color_line}"""

{code}'''
        
        # Write the script file
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        return jsonify({
            "success": True, 
            "script_id": script_id,
            "path": f"{script_id}.py"
        })
    except Exception as e:
        print(f"Error creating script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts/<script_id>', methods=['PUT'])
def update_script(script_id):
    """Update an existing script"""
    try:
        data = request.json
        script_path = os.path.join(SCRIPTS_DIR, f"{script_id}.py")
        
        if not os.path.exists(script_path):
            return jsonify({"success": False, "error": "Script not found"}), 404
        
        # Create the updated script content
        name = data.get('name', 'Unnamed')
        description = data.get('description', 'No description')
        icon = data.get('icon', '🔧')
        color = data.get('color')
        code = data.get('code', '')
        
        color_line = f"Color: {color}\n" if color else ""
        script_content = f'''"""
Name: {name}
Description: {description}
Icon: {icon}
{color_line}"""

{code}'''
        
        # Write the updated script
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts/<script_id>', methods=['DELETE'])
def delete_script(script_id):
    """Delete a script"""
    try:
        script_path = os.path.join(SCRIPTS_DIR, f"{script_id}.py")
        
        if not os.path.exists(script_path):
            return jsonify({"success": False, "error": "Script not found"}), 404
        
        os.remove(script_path)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts/<script_id>/test', methods=['POST'])
def test_script(script_id):
    """Test a script by running it and capturing output"""
    try:
        script_path = os.path.join(SCRIPTS_DIR, f"{script_id}.py")
        
        if not os.path.exists(script_path):
            return jsonify({"success": False, "error": "Script not found"}), 404
        
        # Run the script and capture output
        import subprocess
        import sys
        from io import StringIO
        import contextlib
        
        # Create a StringIO object to capture output
        output = StringIO()
        error_output = StringIO()
        
        try:
            # Read the script content
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # Create a global namespace with built-in modules available
            global_namespace = {
                "__name__": "__main__",
                "__builtins__": __builtins__,
                "webbrowser": __import__("webbrowser"),
                "os": __import__("os"),
                "sys": __import__("sys"),
                "random": __import__("random"),
                "re": __import__("re"),
                "json": __import__("json"),
                "datetime": __import__("datetime"),
                "time": __import__("time"),
                "platform": __import__("platform"),
            }
            
            # Create a local namespace for execution
            local_namespace = {}
            
            # Capture stdout and stderr
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error_output):
                exec(script_content, global_namespace, local_namespace)
                
                # Don't call main() explicitly - let the script handle its own execution
                # The script will run its own if __name__ == "__main__": block
            
            stdout_content = output.getvalue()
            stderr_content = error_output.getvalue()
            
            return jsonify({
                "success": True,
                "output": stdout_content,
                "error": stderr_content if stderr_content else None
            })
            
        except Exception as exec_error:
            return jsonify({
                "success": False,
                "output": output.getvalue(),
                "error": str(exec_error)
            })
    
    except Exception as e:
        print(f"Error testing script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)