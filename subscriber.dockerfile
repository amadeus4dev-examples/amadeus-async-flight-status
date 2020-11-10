FROM python:3

WORKDIR /usr/src

COPY subscriber/subscriber.py subscriber.py
COPY subscriber/requirements.txt requirements.txt
COPY subscriber/static static

RUN pip install -r requirements.txt

CMD [ "python", "./subscriber.py" ]
