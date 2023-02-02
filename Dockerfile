FROM python:3.10.1-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt update

RUN apt install -y adb

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]