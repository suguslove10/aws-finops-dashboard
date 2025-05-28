"""
API for AWS FinOps Dashboard.

This module provides a REST API for the AWS FinOps Dashboard,
allowing the frontend to interact with the dashboard.
"""

import os
import json
import threading
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import configparser

from aws_finops_dashboard.dashboard_runner import run_dashboard
from aws_finops_dashboard.aws_client import get_aws_profiles, get_aws_profiles_with_details, validate_aws_profile, get_account_details
from aws_finops_dashboard.web_ui import run_task_thread, task_results, app as web_app

# Create Flask app
app = Flask(__name__)
# Enable CORS for all routes with all methods
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

# Get output directory from web app config
OUTPUT_DIR = web_app.config['OUTPUT_DIR']
CONFIGS_DIR = os.path.join(OUTPUT_DIR, 'saved_configs')

# Ensure the configs directory exists
os.makedirs(CONFIGS_DIR, exist_ok=True)

@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """Get all available AWS profiles."""
    detail_level = request.args.get('detail', 'basic')
    
    if detail_level == 'full':
        profiles = get_aws_profiles_with_details()
        return jsonify(profiles)
    else:
        profiles = get_aws_profiles()
        return jsonify(profiles)

@app.route('/api/profiles/<profile_name>', methods=['GET'])
def get_profile_details(profile_name):
    """Get detailed information about a specific AWS profile."""
    details = get_account_details(profile_name)
    if details:
        return jsonify(details)
    else:
        # If details can't be retrieved, try basic validation
        validation = validate_aws_profile(profile_name)
        if validation['is_valid']:
            return jsonify(validation)
        else:
            return jsonify({"error": f"Invalid or inaccessible profile: {validation.get('error', 'Unknown error')}"}), 400

@app.route('/api/profiles/<profile_name>/validate', methods=['GET'])
def validate_profile(profile_name):
    """Validate if a profile can be used."""
    validation = validate_aws_profile(profile_name)
    return jsonify(validation)

@app.route('/api/regions', methods=['GET'])
def get_regions():
    """Get all available AWS regions."""
    regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1',
        'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
        'sa-east-1', 'ca-central-1', 'ap-south-1'
    ]
    return jsonify(regions)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all available tasks."""
    tasks = [
        {'id': 'dashboard', 'name': 'Cost Dashboard', 'description': 'Generate a complete AWS cost analysis dashboard'},
        {'id': 'trend', 'name': 'Cost Trend Analysis', 'description': 'Analyze cost trends over time'},
        {'id': 'audit', 'name': 'FinOps Audit', 'description': 'Audit your AWS environment for FinOps best practices'},
        {'id': 'anomalies', 'name': 'Anomaly Detection', 'description': 'Detect cost anomalies in your AWS environment'},
        {'id': 'optimize', 'name': 'Optimization Recommendations', 'description': 'Get recommendations for cost optimization'},
        {'id': 'ri_optimizer', 'name': 'RI & Savings Plan Optimizer', 'description': 'Optimize Reserved Instances and Savings Plans'},
        {'id': 'resource_analyzer', 'name': 'Unused Resource Analyzer', 'description': 'Identify unused or underutilized resources'},
        {'id': 'tag_analyzer', 'name': 'Tag-Based Analysis', 'description': 'Analyze costs by specific tags'}
    ]
    return jsonify(tasks)

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    """Get the list of supported currencies."""
    currencies = [
        {"code": "USD", "name": "US Dollar", "symbol": "$"},
        {"code": "EUR", "name": "Euro", "symbol": "€"},
        {"code": "GBP", "name": "British Pound", "symbol": "£"},
        {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"},
        {"code": "AUD", "name": "Australian Dollar", "symbol": "A$"},
        {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$"},
        {"code": "INR", "name": "Indian Rupee", "symbol": "₹"},
        {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥"},
        {"code": "CHF", "name": "Swiss Franc", "symbol": "Fr"},
        {"code": "BRL", "name": "Brazilian Real", "symbol": "R$"},
        {"code": "MXN", "name": "Mexican Peso", "symbol": "$"},
        {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$"}
    ]
    return jsonify(currencies)

@app.route('/api/save_config', methods=['POST'])
def save_config():
    """Save a task configuration for future use."""
    data = request.json
    
    if not data or 'name' not in data:
        return jsonify({'status': 'error', 'message': 'Configuration name is required'}), 400
    
    # Sanitize the filename
    config_name = data['name'].replace(' ', '_').lower()
    if not config_name.endswith('.json'):
        config_name += '.json'
    
    config_path = os.path.join(CONFIGS_DIR, config_name)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        return jsonify({'status': 'success', 'message': 'Configuration saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/saved_configs', methods=['GET'])
def get_saved_configs():
    """Get all saved configurations."""
    configs = []
    
    try:
        for filename in os.listdir(CONFIGS_DIR):
            if filename.endswith('.json'):
                config_path = os.path.join(CONFIGS_DIR, filename)
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Add filename to the config
                    config['filename'] = filename
                    configs.append(config)
        return jsonify(configs)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/load_config/<filename>', methods=['GET'])
def load_config(filename):
    """Load a saved configuration."""
    config_path = os.path.join(CONFIGS_DIR, filename)
    
    if not os.path.exists(config_path):
        return jsonify({'status': 'error', 'message': 'Configuration not found'}), 404
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/delete_config/<filename>', methods=['DELETE'])
def delete_config(filename):
    """Delete a saved configuration."""
    config_path = os.path.join(CONFIGS_DIR, filename)
    
    if not os.path.exists(config_path):
        return jsonify({'status': 'error', 'message': 'Configuration not found'}), 404
    
    try:
        os.remove(config_path)
        return jsonify({'status': 'success', 'message': 'Configuration deleted successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/run_task', methods=['POST'])
def run_task():
    """Run a task."""
    data = request.json

    # Create args object
    args = type('Args', (), {
        'profiles': data.get('profiles', []),
        'all': not data.get('profiles'),
        'regions': data.get('regions', []),
        'combine': data.get('combine', False),
        'report_name': data.get('report_name', f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
        'report_type': data.get('formats', []),
        'dir': OUTPUT_DIR,
        'time_range': int(data.get('time_range', 30)),
        'tag': data.get('tags', []),  # Support for tag-based filtering
        'trend': data.get('task_type') == 'trend',
        'audit': data.get('task_type') == 'audit',
        'detect_anomalies': data.get('task_type') == 'anomalies',
        'anomaly_sensitivity': float(data.get('anomaly_sensitivity', 0.05)),
        'optimize': data.get('task_type') == 'optimize',
        'cpu_threshold': float(data.get('cpu_threshold', 40.0)),
        'skip_ri_analysis': data.get('skip_ri_analysis', False),
        'skip_savings_plans': data.get('skip_savings_plans', False),
        'currency': data.get('currency', 'USD'),
        'enhanced_pdf': data.get('enhanced_pdf', False),
        'ri_optimizer': data.get('task_type') == 'ri_optimizer',
        'resource_analyzer': data.get('task_type') == 'resource_analyzer',
        'resource_types': data.get('resource_types', ['all']),
        'lookback_days': int(data.get('lookback_days', 30)),
        'tag_analyzer': data.get('task_type') == 'tag_analyzer',
        'config_file': None
    })

    # Create a new thread to run the task
    task_type = data.get('task_type', 'dashboard')
    task_thread = threading.Thread(target=run_task_thread, args=(args, task_type))
    task_thread.daemon = True
    task_thread.start()

    return jsonify({'status': 'running', 'task_type': task_type})

@app.route('/api/task_status', methods=['GET'])
def task_status():
    """Get the status of the current task."""
    task_type = request.args.get('task_type', 'dashboard')
    format_type = request.args.get('format', 'raw')  # 'raw' or 'html'
    
    if task_type in task_results:
        result = task_results[task_type]
        
        # Original raw output
        raw_output = result['output']
        
        # Only format if HTML format is requested
        if format_type == 'html':
            # Format the output for better display
            formatted_output = raw_output
            
            # If the output contains terminal-style ASCII art or tables, process it
            if '$$\\' in formatted_output or '/$$' in formatted_output or '+----+' in formatted_output:
                from aws_finops_dashboard.web_ui import format_output_for_web, convert_ansi_to_html
                
                # First convert any ANSI color codes
                formatted_output = convert_ansi_to_html(formatted_output)
                
                # Then handle table formatting
                formatted_output = format_output_for_web(formatted_output)
            
            output = formatted_output
        else:
            # Return raw output
            output = raw_output
        
        return jsonify({
            'status': result['status'],
            'output': output,
            'files': result['files']
        })
    
    return jsonify({
        'status': 'not_found',
        'output': '',
        'files': []
    })

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get all generated files."""
    files = []
    for fname in os.listdir(OUTPUT_DIR):
        if os.path.isfile(os.path.join(OUTPUT_DIR, fname)):
            files.append(fname)
    return jsonify(files)

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/profiles/add', methods=['POST', 'OPTIONS'])
def add_profile():
    """Add a new AWS profile credential."""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    required_fields = ['profile_name', 'aws_access_key_id', 'aws_secret_access_key']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    profile_name = data['profile_name']
    aws_access_key_id = data['aws_access_key_id']
    aws_secret_access_key = data['aws_secret_access_key']
    region = data.get('region', 'us-east-1')
    
    # Check if profile already exists
    existing_profiles = get_aws_profiles()
    if profile_name in existing_profiles:
        return jsonify({'error': f'Profile {profile_name} already exists'}), 400
    
    try:
        # Try first with the configparser approach
        success = add_profile_with_configparser(profile_name, aws_access_key_id, aws_secret_access_key, region)
        
        if not success:
            # If that fails, try with the AWS CLI
            success = add_profile_with_aws_cli(profile_name, aws_access_key_id, aws_secret_access_key, region)
            
            if not success:
                return jsonify({'error': 'Could not add profile using any available method'}), 500
        
        # Validate the new profile
        validation = validate_aws_profile(profile_name)
        if not validation.get('is_valid', False):
            # If validation fails, return the credentials but with a warning
            return jsonify({
                'profile_name': profile_name,
                'status': 'added_with_warning',
                'warning': 'Credentials were saved but could not be validated. They may be incorrect or have insufficient permissions.',
                'validation_error': validation.get('error', 'Unknown error')
            })
            
        return jsonify({'profile_name': profile_name, 'status': 'success'})
    except Exception as e:
        return jsonify({'error': f'Failed to add profile: {str(e)}'}), 500

def add_profile_with_configparser(profile_name, aws_access_key_id, aws_secret_access_key, region):
    """Add AWS profile using configparser."""
    try:
        # Update AWS credentials file
        credentials_path = os.path.expanduser("~/.aws/credentials")
        os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
        
        # Check write permissions for credentials file
        if os.path.exists(credentials_path) and not os.access(credentials_path, os.W_OK):
            print(f"No write permission for AWS credentials file: {credentials_path}")
            return False
            
        # Check write permissions for directory
        aws_dir = os.path.dirname(credentials_path)
        if not os.access(aws_dir, os.W_OK):
            print(f"No write permission for AWS directory: {aws_dir}")
            return False
        
        config = configparser.ConfigParser()
        if os.path.exists(credentials_path):
            config.read(credentials_path)
            
        if profile_name not in config:
            config[profile_name] = {}
            
        config[profile_name]['aws_access_key_id'] = aws_access_key_id
        config[profile_name]['aws_secret_access_key'] = aws_secret_access_key
        
        with open(credentials_path, 'w') as f:
            config.write(f)
            
        # Update AWS config file with region
        config_path = os.path.expanduser("~/.aws/config")
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path)
            
        # AWS config uses 'profile profile_name' format except for 'default'
        section_name = profile_name
        if profile_name != 'default':
            section_name = f'profile {profile_name}'
            
        if section_name not in config:
            config[section_name] = {}
            
        config[section_name]['region'] = region
        
        with open(config_path, 'w') as f:
            config.write(f)
            
        return True
    except Exception as e:
        print(f"Error adding profile with configparser: {str(e)}")
        return False

def add_profile_with_aws_cli(profile_name, aws_access_key_id, aws_secret_access_key, region):
    """Add AWS profile using the AWS CLI."""
    try:
        # Use AWS CLI to set credentials
        subprocess.run([
            'aws', 'configure', 'set', 
            f'--profile={profile_name}', 
            'aws_access_key_id', 
            aws_access_key_id
        ], check=True)
        
        subprocess.run([
            'aws', 'configure', 'set', 
            f'--profile={profile_name}', 
            'aws_secret_access_key', 
            aws_secret_access_key
        ], check=True)
        
        subprocess.run([
            'aws', 'configure', 'set', 
            f'--profile={profile_name}', 
            'region', 
            region
        ], check=True)
        
        return True
    except Exception as e:
        print(f"Error adding profile with AWS CLI: {str(e)}")
        return False

def run_api(host='0.0.0.0', port=5001):
    """Run the API server."""
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_api() 