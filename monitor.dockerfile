FROM python:3

WORKDIR /usr/src

ENV AMADEUS_CLIENT_ID $AMADEUS_CLIENT_ID
ENV AMADEUS_CLIENT_SECRET $AMADEUS_CLIENT_SECRET

COPY monitor/monitor.py monitor.py
COPY monitor/requirements.txt requirements.txt

RUN pip install -r requirements.txt

CMD [ "python", "./monitor.py" ]
