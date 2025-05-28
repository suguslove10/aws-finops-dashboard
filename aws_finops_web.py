#!/usr/bin/env python3
"""
AWS FinOps Dashboard Web UI.

This script launches the web interface for the AWS FinOps Dashboard,
allowing users to interact with the tool through a browser.
"""

import sys
from aws_finops_dashboard.web_ui import run_server

if __name__ == "__main__":
    print("Starting AWS FinOps Dashboard Web UI...")
    run_server(host='0.0.0.0', port=3001, open_browser=True) 