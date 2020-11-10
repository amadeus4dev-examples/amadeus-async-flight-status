import os
import ast
import datetime
import twilio.rest as twilio
import paho.mqtt.client as mqtt

def build_message(user, departure, arrival):

    fmt = '%Y-%m-%d %H:%M'

    departure_time = datetime.datetime.strptime(departure['scheduledDate'], fmt).strftime('%H:%M')
    arrival_time = datetime.datetime.strptime(arrival['scheduledDate'], fmt).strftime('%H:%M')

    msg  = "Dear {}, your flight from {} to {} has been updated: ".format(user['userName'],
                                                                        departure['iataCode'],
                                                                        arrival['iataCode'])
    msg += "departure at {}".format(departure_time)

    if departure['terminal']:
        msg += " terminal {}".format(departure['terminal'])
    if departure['gate']:
        msg += " gate {}".format(departure['gate'])

    msg += ". Arrival at {}".format(arrival_time)

    if arrival['terminal']:
        msg += " terminal {}".format(arrival['terminal'])
    if arrival['gate']:
        msg += " gate {}".format(arrival['gate'])


    msg += ". Enjoy your flight!"

    return msg

def on_connect(client, userdata, flags, rc):
    client.subscribe("flight/update")

def on_message(client, userdata, msg):
    msg_str = msg.payload.decode("UTF-8")
    alert_msg = ast.literal_eval(msg_str)

    account_sid = os.getenv('TWILIO_SID', None)
    auth_token = os.getenv('TWILIO_TOKEN', None)
    twilio_phone = os.getenv('TWILIO_NUMBER', None)

    if not account_sid or not auth_token or not twilio_phone:
        return

    client = twilio.Client(account_sid, auth_token)

    msg = build_message(alert_msg['user'],
                        alert_msg['departure'],
                        alert_msg['arrival'])

    destination_phone = alert_msg['user']['phoneNumber']

    message = client.messages.create(body=msg,
                                     from_=twilio_phone,
                                     to=destination_phone
                                     )

if __name__ == "__main__":

    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("broker", 1883, 60)
    except ConnectionRefusedError:
        print("Error: Unable to connect to broker")
    client.loop_forever()
