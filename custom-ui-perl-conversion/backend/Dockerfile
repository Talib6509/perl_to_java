FROM python:3.9-slim-buster

WORKDIR /api

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=False

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]