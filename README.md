# Backend—Smart Traffic Lights Controller

Setup:

    Creating venv:
    
        sudo apt install python3-venv
        python3 -m venv venv ( <- environment name )
        source .venv/bin/activate

    Installing required packages:
        pip install -r requirements.txt && pip install -r pytorch_requirements.txt

    Running docker:
        sudo docker run -p 8000:8000 --gpus all -it django-docker
    
    Clean docker images cache & tmps:
        docker system prune -f
