FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install all required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    pandas \
    numpy \
    scikit-learn \
    matplotlib \
    boto3 \
    rich \
    requests \
    reportlab \
    pyyaml \
    tomli \
    flask \
    flask-cors

# Copy the backend code
COPY aws_finops_dashboard/ ./aws_finops_dashboard/

# Create directories for outputs
RUN mkdir -p /app/output

# Expose the API port
EXPOSE 5001

# Run the API server
CMD ["python", "-m", "aws_finops_dashboard.api"] 