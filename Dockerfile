# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for OpenCV and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# Using tensorflow-cpu for smaller image size and compatibility
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir tensorflow-cpu && \
    pip install --no-cache-dir -r requirements.txt

# Download NLP models
RUN python -m spacy download en_core_web_sm && \
    python -m nltk.downloader punkt stopwords

# Copy the rest of the application code
COPY . .

# Create directory for database and temp images
RUN mkdir -p data/Data/train models

# Expose the ports for Streamlit and FastAPI
EXPOSE 8501 8000

# Entry point will be handled by docker-compose
CMD ["python", "app.py"]
