FROM python:3

WORKDIR /usr/src

COPY notifier/notifier.py notifier.py
COPY notifier/requirements.txt requirements.txt

RUN pip install -r requirements.txt

CMD [ "python", "./notifier.py" ]
