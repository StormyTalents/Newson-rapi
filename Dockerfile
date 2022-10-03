FROM python:3.8.3-slim-buster

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y python3-dev build-essential python3-dev wget xvfb python3-tk
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update && apt-get install -y google-chrome-stable


# set display port to avoid crash
ENV DISPLAY=:99

RUN ls -la

COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

RUN ["chmod", "+x", "/usr/src/app/entrypoint.sh"]

COPY ./ ./

ENTRYPOINT ["sh", "/usr/src/app/entrypoint.sh"]
