FROM python:3.11

WORKDIR /app

# Install nano and screen
RUN apt-get update && apt-get install -y \
    nano \
    screen \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python3","-u", "main.py"]
