import time
import json
import ast
import threading
import amadeus
import datetime
import paho.mqtt.client as mqtt

flights = {}

payload_fmt = '%Y-%m-%d %H:%M'

def on_connect(client, userdata, flags, rc):
    client.subscribe("flight/queue")


def on_message(client, userdata, msg):
    msg_str = msg.payload.decode("UTF-8")
    queue_msg = ast.literal_eval(msg_str)

    flight = queue_msg['flight']
    user = queue_msg['user']

    # Build key out of the elements from incoming message
    key = "{}#{}#{}#{}#{}".format(flight['carrierCode'],
                            flight['flightNumber'],
                            flight['scheduledDepartureDate'],
                            user['userName'],
                            user['phoneNumber'])


    flight_status = {
        'departure': {'iataCode': None,
                      'scheduledDate': None,
                      'terminal': None,
                      'gate': None},
        'arrival': {'iataCode': None,
                    'scheduledDate': None,
                    'terminal' : None,
                    'gate': None}
    }

    flights[key] = {
        'user': user,
        'departure': flight_status['departure'],
        'arrival': flight_status['arrival']
    }

def update_flight(client, flight):

    (code, number, date, user, phone) = flight.split('#')
    response = client.schedule.flights.get(
                             carrierCode=code,
                             flightNumber=number,
                             scheduledDepartureDate=date
    )
    updated = False

    flight_status = flights[flight]

    body = json.loads(response.body)

    if 'data' in body:
        for dated_flight in body['data']:
            if 'flightPoints' in dated_flight:
                for flight_point in dated_flight['flightPoints']:

                    if 'arrival' in flight_point:
                        action = 'arrival'
                    elif 'departure'  in flight_point:
                        action = 'departure'
                    else:
                        continue

                    flight_action = flight_point[action]

                    flight_status[action]['iataCode'] = flight_point['iataCode']

                    action_date, action_time = flight_action['timings'][0]['value'].split('T')

                    if '+' in action_time:
                        action_time = action_time.split('+')[0]
                    else:
                        action_time = action_time.split('-')[0]

                    action_datetime = datetime.datetime.strptime("{} {}".format(action_date, action_time), payload_fmt)

                    if flight_status[action]['scheduledDate'] != action_datetime:
                        updated = True

                    flight_status[action]['scheduledDate'] = action_datetime

                    if 'terminal' in flight_point[action]:

                        if flight_status[action]['terminal'] != flight_action['terminal']['code']:
                            updated = True

                        flight_status[action]['terminal'] = flight_action['terminal']['code']

                    if 'gate' in flight_point[action]:

                        if flight_status[action]['gate'] != flight_action['gate']['mainGate']:
                                updated = True

                        flight_status[action]['gate'] = flight_action['gate']['mainGate']

    return updated

def needs_update(flight):

    hours_to_monitor = 4


    # always update newerly incoming flights
    if not flights[flight]['departure']['scheduledDate']:
        return True

    departure_date = flights[flight]['departure']['scheduledDate']
    current_date = datetime.datetime.now()

    # we monitor only the departure date
    if current_date.date() == departure_date.date():

        delta = (departure_date - current_date).total_seconds() / 3600

        # Keep monitoring if we are 4 hours away from departure time
        if delta <= hours_to_monitor:
            return True

    return False

def payload2str(payload):

    return str({'user': payload['user'],
                'departure': {'iataCode': payload['departure']['iataCode'],
                              'scheduledDate': payload['departure']['scheduledDate'].strftime(payload_fmt),
                              'terminal': payload['departure']['terminal'],
                              'gate': payload['departure']['gate'],
                              },
                'arrival': {'iataCode': payload['arrival']['iataCode'],
                              'scheduledDate': payload['arrival']['scheduledDate'].strftime(payload_fmt),
                              'terminal': payload['arrival']['terminal'],
                              'gate': payload['arrival']['gate'],
                              }
                })

class FlightStatusMonitor(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.running = True
        self.mqtt_client = client
        self.amadeus = amadeus.Client()

    def run(self):
        while self.running:
            for flight in flights:
                if needs_update(flight):
                    updated = update_flight(self.amadeus, flight)

                    if updated:
                        print('alerting...')
                        self.mqtt_client.publish('flight/update', payload = payload2str(flights[flight].copy()))

            # sleep for 5 minutes
            time.sleep(60*5)

    def stop(self):
        self.running = False

if __name__ == "__main__":

    client = mqtt.Client()

    status_monitor = FlightStatusMonitor(client)
    status_monitor.start()

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("broker", 1883, 60)
    except ConnectionRefusedError:
        print("Error: Unable to connect to broker")
    client.loop_forever()

