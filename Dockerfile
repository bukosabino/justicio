FROM python:3.11-slim-buster

RUN apt-get update && apt-get install -y \
    curl \
    libssl-dev \
    unzip \
    htop \
    jq \
    lynx \
    p7zip-full \
    procps \
    screen \
    vim \
 && rm -rf /var/lib/apt/lists/* \

# RUN pip install --upgrade pip

WORKDIR /usr/app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

ENV APP_PATH="/usr/app"
ENV PYTHONPATH "${PYTHONPATH}:${APP_PATH}"

CMD ["python", "src/etls/etl_initial.py"]
