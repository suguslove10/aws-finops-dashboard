# AWS FinOps Dashboard UI

A modern Next.js frontend for the AWS FinOps Dashboard, providing a clean and intuitive user interface for AWS cost optimization and analysis.

## Features

- Clean, modern UI built with Next.js and Tailwind CSS
- Interactive dashboard for AWS FinOps tasks
- Real-time task status updates
- Responsive design for all device sizes
- Terminal-like output display with proper formatting
- Easy file downloads

## Prerequisites

- Node.js 18.0.0 or later
- npm or yarn
- Python 3.7 or later (for the backend API)
- AWS CLI configured with your credentials

## Getting Started

### 1. Install dependencies:

```bash
# Install frontend dependencies
cd frontend/aws-finops-ui
npm install
```

### 2. Start the application:

There are two ways to start the application:

#### Option 1: Using the start script (recommended)

From the project root directory:

```bash
./start.sh
```

This will start both the Flask API server and the Next.js frontend.

#### Option 2: Starting separately

Terminal 1 (API server):
```bash
python -m aws_finops_dashboard.api
```

Terminal 2 (Next.js frontend):
```bash
cd frontend/aws-finops-ui
npm run dev
```

### 3. Access the dashboard:

Open your browser and navigate to:

```
http://localhost:3000
```

## Development

- The frontend is built with Next.js and Tailwind CSS
- API requests are handled with Axios and React Query
- UI components are built with Tremor and styled with Tailwind
- Terminal-like output is handled with styled pre tags and proper HTML formatting

## Folder Structure

```
frontend/aws-finops-ui/
├── src/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # Reusable UI components
│   ├── lib/                 # Utilities and API client
│   └── ...
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
└── ...
```

## API Integration

The frontend communicates with the Flask API server running on port 5000. The API client is located in `src/lib/api.ts` and handles all the requests to the server.
