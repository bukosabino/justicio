FROM python:3.11-slim

RUN pip install --upgrade pip

WORKDIR /usr/app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

ENV APP_PATH="/usr/app"
ENV PYTHONPATH "${PYTHONPATH}:${APP_PATH}"

CMD ["uvicorn", "src.service.app:APP", "--host", "0.0.0.0", "--port", "5000", "--workers", "2", "--timeout-keep-alive", "125", "--log-level", "info"]
