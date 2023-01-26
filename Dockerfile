FROM python:3.10-alpine

RUN apk update && apk add --no-cache build-base python3-dev

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "main.py"]