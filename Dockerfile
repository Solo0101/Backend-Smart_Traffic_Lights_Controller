# Use the official Python runtime image
FROM python:3.10
# Choose an appropriate NVIDIA CUDA base image
# Replace with the specific CUDA version and distribution you need
#FROM nvidia/cuda:12.8.0-devel-ubuntu24.04
FROM nvidia/cuda:12.8.0-base-ubuntu24.04

# Set environment variables

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all

# Create the app directory
RUN mkdir /app

# Set the working directory in the container
WORKDIR /app

# Install Python, pip, and common dependencies
# (Some NVIDIA images might already have Python. Adjust as needed.)

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    software-properties-common \
    ca-certificates \
    build-essential \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.10 \
        python3.10-dev \
        python3.10-venv \
        python3.10-distutils \
        ffmpeg \
        libsm6 \
        libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.10 and upgrade it
RUN python3.10 -m ensurepip \
    && python3.10 -m pip install --no-cache-dir --upgrade pip setuptools wheel opencv-python-headless

# Create a virtual envir
# Link python3 to python and pip3 to pip if necessary (common in some base images)
#RUN ln -s /usr/bin/python3 /usr/bin/python && \
#    ln -s /usr/bin/pip3 /usr/bin/pip

# Create a virtual environment
ENV VENV_PATH=/opt/venv
RUN python3.10 -m venv $VENV_PATH

ENV PATH="$VENV_PATH/bin:$PATH"

# Copy the requirements file into the container
COPY requirements.txt /app/
COPY pytorch_requirements.txt /app/

# Install Python dependencies
# Ensure your requirements.txt specifies GPU-enabled versions of libraries
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r pytorch_requirements.txt

# Copy your Django project code into the container
COPY . .

# Expose the port your Django app runs on (e.g., 8000)
#EXPOSE 8000 8001
EXPOSE 8000

# Command to run your application
# For development (less secure, not for production):
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# For production (using Gunicorn or another WSGI server):
#CMD ["gunicorn","–config=gunicorn_config.py","stream.wsgi:application"]
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "stream.wsgi:application"]

# For production (using Daphne or another ASGI server):
#CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "stream.asgi:application"]
#CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "stream.asgi:application"]
