#!/bin/bash

# Start API server in the background
echo "Starting API server..."
cd "$(dirname "$0")"
python -m aws_finops_dashboard.api &
API_PID=$!

# Start Next.js frontend
echo "Starting Next.js frontend..."
cd frontend/aws-finops-ui
npm run dev

# Cleanup on exit
trap 'kill $API_PID' EXIT 