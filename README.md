# 🚦 Backend—Smart Traffic Lights Controller

This repository contains the backend for the **Smart Traffic Lights Controller** application, a system designed to optimize traffic flow in real-time using computer vision and reinforcement learning.

---

## ✨ Features

-   **Real-time Traffic Analysis:** Uses YOLO for object detection to identify and track vehicles, bicycles, and pedestrians.
-   **Dynamic Traffic Light Control:** Employs a Deep Q-Network with Prioritized Experience Replay (DQN-PER) to make intelligent decisions for traffic light control.
-   **Web-Based Interface:** Provides a web interface to monitor the video stream from the traffic camera.
-   **RESTful API:** Offers a comprehensive API to manage intersections, view statistics, and control traffic lights.
-   **WebSocket Communication:** Enables real-time communication with the Raspberry Pi controlling the traffic lights.
-   **Dockerized Deployment:** Includes a `docker-compose.yml` file for easy setup and deployment.

---

## 🛠️ Tech Stack

-   **Backend:** Django, Django REST Framework, Channels
-   **Machine Learning:** PyTorch, OpenCV
-   **Database:** PostgreSQL with PostGIS
-   **Caching:** Redis
-   **Web Server:** Gunicorn, Daphne, Nginx (optional)
-   **Containerization:** Docker

---

## ⚙️ Setup and Installation

You can set up the project locally or by using Docker.

### For Local Development

1.  **Install Python 3.10**.
2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install the required packages**:
    ```bash
    pip install -r requirements.txt
    pip install -r pytorch_requirements.txt
    ```
4.  **Install Additional Services**:
    You will need to install and run the following open-source services:
    -   Redis
    -   PostGIS
    -   Nginx (optional)
5.  **Run the application**:
    -   **On Linux**:
        ```bash
        bash ./run.sh
        ```
    -   **On Windows**:
        ```bash
        python manage.py makemigrations webcam --noinput
        python manage.py migrate --noinput
        python manage.py runserver 0.0.0.0:8000 --noreload
        ```

### Using Docker 🐳

1.  **(Optional) Install NVIDIA CUDA Toolkit** for GPU acceleration.
2.  **(Optional) Install NVIDIA Container Toolkit** to use the GPU within Docker containers.
3.  **Install Docker and Docker-Compose**.
4.  **From the project directory, run**:
    ```bash
    docker-compose up
    ```

**Note**: For a connection with a Raspberry Pi over WAN, a service like `Remote.it` can be used to create a secure tunnel.

---

## 📜 API Endpoints

The application exposes several API endpoints for managing intersections and traffic lights. For a full list of available endpoints and their specifications, please refer to the `webcam/urls.py` file.

---

## 📂 Project Structure

.├── stream/             # Django project configuration├── webcam/             # Main Django application│   ├── migrations/│   ├── models/         # YOLO model files│   ├── templates/      # HTML templates│   ├── dqn_per.py      # Deep Q-Network implementation│   ├── models.py       # Django models│   ├── serializers.py  # API serializers│   ├── urls.py         # Application-specific URLs│   └── views.py        # API views├── docker-compose.yml├── manage.py├── README.md├── requirements.txt└── run.sh
---

## 📄 License

This project is licensed under the MIT License.
