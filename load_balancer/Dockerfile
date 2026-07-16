FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y sudo curl && curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

RUN pip install flask requests

COPY hash_ring.py .
COPY lb_app.py .

EXPOSE 5000

CMD ["python", "lb_app.py"]
