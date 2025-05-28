"""
Web UI for AWS FinOps Dashboard.

This module provides a REST API for the AWS FinOps Dashboard frontend.
"""

import os
import sys
import threading
import tempfile
import json
from datetime import datetime
import argparse
from io import StringIO
from typing import Dict, Any, List, Optional
import re
from rich.console import Console as RichConsole
from rich.text import Text

import boto3
from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS

from aws_finops_dashboard.aws_client import get_aws_profiles
from aws_finops_dashboard.dashboard_runner import run_dashboard
from aws_finops_dashboard.ri_optimizer import RIOptimizer
from aws_finops_dashboard.resource_analyzer import UnusedResourceAnalyzer

app = Flask(__name__)
CORS(app)  # Enable CORS for API access
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['OUTPUT_DIR'] = os.path.join(tempfile.gettempdir(), 'aws_finops_dashboard')

# Ensure output directory exists
os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)

# Global variables to store task results
task_results = {}
available_profiles = []

def format_output_for_web(output_text):
    """
    Format console output for better display in web UI.
    
    Args:
        output_text: Raw console output text
        
    Returns:
        Formatted HTML output
    """
    # Check if output already contains HTML tables
    if '<table' in output_text and '</table>' in output_text:
        # Clean up any broken HTML tags in the output
        output_text = re.sub(r'<(/?)tr[^>]*>', r'<\1tr>', output_text)
        output_text = re.sub(r'<(/?)td[^>]*>', r'<\1td>', output_text)
        output_text = re.sub(r'<(/?)th[^>]*>', r'<\1th>', output_text)
        
        # Add Bootstrap classes to tables
        output_text = output_text.replace('<table', '<table class="aws-cli-table"')
        output_text = output_text.replace('</table>', '</table>')
        
        return output_text
    
    # Convert ASCII tables to HTML tables
    lines = output_text.split('\n')
    formatted_output = []
    in_table = False
    current_table = []
    header_row = []
    
    for line in lines:
        # Table detection - look for lines with multiple pipe characters or +----+ patterns
        if ('|' in line and line.count('|') > 2) or ('+' in line and '-' in line and line.count('+') > 2):
            if not in_table:
                in_table = True
                # Start a new table
                current_table = []
                header_row = []
            
            # Skip separator lines
            if '+' in line and '-' in line and '+' in line:
                continue
            
            # Process table row
            if '|' in line:
                # Extract cells from the row
                cells = [cell.strip() for cell in line.split('|')]
                # Remove empty cells at start/end
                if cells and not cells[0]:
                    cells = cells[1:]
                if cells and not cells[-1]:
                    cells = cells[:-1]
                    
                # Store row
                if not header_row and cells:
                    header_row = cells
                else:
                    current_table.append(cells)
        else:
            # Not a table row
            if in_table:
                # End of table, convert to HTML
                table_html = '<table class="aws-cli-table">'
                
                # Add header
                if header_row:
                    table_html += '<thead><tr>'
                    for cell in header_row:
                        table_html += f'<th>{escape_html(cell)}</th>'
                    table_html += '</tr></thead>'
                
                # Add body
                table_html += '<tbody>'
                for row in current_table:
                    table_html += '<tr>'
                    for cell in row:
                        table_html += f'<td>{escape_html(cell)}</td>'
                    table_html += '</tr>'
                table_html += '</tbody></table>'
                
                formatted_output.append(table_html)
                in_table = False
                current_table = []
                header_row = []
            
            # Detect and format AWS account IDs for better readability
            line = re.sub(r'(\d{12})', r'<span class="badge bg-secondary">\1</span>', line)
            
            # Process line with colors
            line = line.replace('[green]', '<span class="text-success">')
            line = line.replace('[red]', '<span class="text-danger">')
            line = line.replace('[yellow]', '<span class="text-warning">')
            line = line.replace('[cyan]', '<span class="text-info">')
            line = line.replace('[blue]', '<span class="text-primary">')
            line = line.replace('[/]', '</span>')
            line = line.replace('[bold]', '<strong>')
            line = line.replace('[/bold]', '</strong>')
            
            # Handle AWS CLI ASCII art for better display
            if "$$\\" in line or "/$$" in line or "_/" in line or "\\__" in line:
                line = f'<pre>{line}</pre>'
                
            formatted_output.append(line)
    
    # Handle any remaining table
    if in_table and (current_table or header_row):
        table_html = '<table class="aws-cli-table">'
        
        # Add header
        if header_row:
            table_html += '<thead><tr>'
            for cell in header_row:
                table_html += f'<th>{escape_html(cell)}</th>'
            table_html += '</tr></thead>'
        
        # Add body
        table_html += '<tbody>'
        for row in current_table:
            table_html += '<tr>'
            for cell in row:
                table_html += f'<td>{escape_html(cell)}</td>'
            table_html += '</tr>'
        table_html += '</tbody></table>'
        
        formatted_output.append(table_html)
    
    # Format any AWS CLI command outputs
    output_text = '\n'.join(formatted_output)
    
    return output_text


def escape_html(text):
    """
    Escape HTML special characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        HTML-escaped text
    """
    if not text:
        return ""
    
    return (str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def run_task_thread(args, task_type):
    """Run a task in a separate thread and capture its output."""
    global task_results
    
    class AnsiPreservingStringIO(StringIO):
        def write(self, text):
            # This preserves ANSI escape codes in the output
            return super().write(text)
    
    try:
        # Initialize task result with a nicer starting message
        task_results[task_type] = {
            'status': 'running',
            'output': f'\x1b[34;1mStarting {task_type} task...\x1b[0m\n' +
                      f'\x1b[36mTask is initializing, please wait...\x1b[0m\n',
            'files': []
        }
        
        # Capture stdout
        old_stdout = sys.stdout
        output_capture = AnsiPreservingStringIO()
        sys.stdout = output_capture
        
        # Update status with more information
        task_results[task_type]['output'] += f'\x1b[36mInitializing AWS resources...\x1b[0m\n'
        
        # Run appropriate task
        if task_type == 'ri_optimizer':
            task_results[task_type]['output'] += f'\x1b[36mStarting Reserved Instance Optimizer...\x1b[0m\n'
            optimizer = RIOptimizer(
                profiles=args.profiles,
                use_all_profiles=args.all,
                lookback_days=args.lookback_days,
                output_dir=args.dir,
                report_name=args.report_name,
                report_format=args.report_type
            )
            optimizer.run()
        elif task_type == 'resource_analyzer':
            task_results[task_type]['output'] += f'\x1b[36mStarting Unused Resource Analyzer...\x1b[0m\n'
            analyzer = UnusedResourceAnalyzer(
                profiles=args.profiles,
                use_all_profiles=args.all,
                regions=args.regions,
                resource_types=args.resource_types,
                output_dir=args.dir,
                report_name=args.report_name,
                report_format=args.report_type
            )
            analyzer.run()
        else:
            # Run standard dashboard
            task_results[task_type]['output'] += f'\x1b[36mRunning AWS FinOps Dashboard...\x1b[0m\n'
            run_dashboard(args)
        
        # Restore stdout
        sys.stdout = old_stdout
        raw_output = output_capture.getvalue()
        
        # Get generated files
        files = []
        for fname in os.listdir(args.dir):
            if os.path.isfile(os.path.join(args.dir, fname)) and args.report_name in fname:
                files.append(fname)
        
        # Add a completion message
        completion_message = '\x1b[32;1m✅ Task completed successfully!\x1b[0m\n'
        if files:
            completion_message += '\x1b[34m📁 Files were generated. You can download them below.\x1b[0m\n'
        
        # Update task result
        task_results[task_type] = {
            'status': 'completed',
            'output': completion_message + raw_output,
            'files': files
        }
    
    except Exception as e:
        # Handle errors
        sys.stdout = old_stdout if 'old_stdout' in locals() else sys.stdout
        error_output = f'\x1b[31;1m❌ Error running {task_type} task: {str(e)}\x1b[0m\n'
        if 'output_capture' in locals():
            error_output += output_capture.getvalue()
        
        # Update task result with error
        task_results[task_type] = {
            'status': 'error',
            'output': error_output,
            'files': []
        }


@app.route('/api/task_results')
def get_task_results():
    """Get the results of the current task."""
    task_type = request.args.get('task_type', 'dashboard')
    if task_type in task_results:
        return jsonify(task_results[task_type])
    return jsonify({'status': 'not_found', 'output': '', 'files': []})


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a generated file."""
    return send_from_directory(app.config['OUTPUT_DIR'], filename, as_attachment=True)


@app.route('/api/files')
def get_files():
    """Get all generated files."""
    files = []
    for fname in os.listdir(app.config['OUTPUT_DIR']):
        if os.path.isfile(os.path.join(app.config['OUTPUT_DIR'], fname)):
            files.append(fname)
    return jsonify(files)


@app.route('/api/currencies')
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
    ]
    return jsonify(currencies)


@app.route('/api/run_task', methods=['POST'])
def api_run_task():
    """Run a task from the API."""
    data = request.get_json()
    task_type = data.get('task_type', 'dashboard')
    
    # Create args object to pass to run_task_thread
    class Args:
        pass
    
    args = Args()
    args.profiles = data.get('profiles', [])
    args.all = False
    args.regions = data.get('regions', [])
    args.dir = app.config['OUTPUT_DIR']
    args.report_name = data.get('report_name', f'report_{datetime.now().strftime("%Y-%m-%d")}')
    args.report_type = data.get('formats', ['csv'])
    args.lookback_days = data.get('lookback_days', 30)
    args.resource_types = data.get('resource_types', [])
    args.currency = data.get('currency', 'USD')
    
    # Start the task in a background thread
    thread = threading.Thread(target=run_task_thread, args=(args, task_type))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "task_type": task_type})


def run_server(host='127.0.0.1', port=5001, debug=False, open_browser=False):
    """Run the Flask server."""
    global available_profiles
    available_profiles = get_aws_profiles()
    
    if open_browser:
        webbrowser.open(f'http://{host}:{port}')
    
    app.run(host=host, port=port, debug=debug)


def main():
    """Run the web UI."""
    parser = argparse.ArgumentParser(description='Run AWS FinOps Dashboard Web UI')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, debug=args.debug, open_browser=not args.no_browser)


if __name__ == '__main__':
    main() 