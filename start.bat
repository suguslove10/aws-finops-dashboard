@echo off
echo Starting API server...
start /b python -m aws_finops_dashboard.api
 
echo Starting Next.js frontend...
cd frontend\aws-finops-ui
npm run dev 