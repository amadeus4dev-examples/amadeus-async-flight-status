import flask
import paho.mqtt.client as mqtt

app = flask.Flask(__name__)

client = None

@app.route('/subscribe',methods= ['POST'])
def subscribe():
    """
    Payload example:

    {
      "flight": {
        "carrierCode": "LH",
        "flightNumber": "193",
        "scheduledDepartureDate": "2020-10-20"
      },
      "user": {
        "userName": "John Smith",
        "phoneNumber": "+13451235"
      }
    }
    """
    form_dict = flask.request.form.to_dict()

    client.publish("flight/queue", str(
        {
            'flight': {
                'carrierCode':form_dict['carrier'],
                'flightNumber':form_dict['flightnumber'],
                'scheduledDepartureDate':form_dict['departuredate']
            },
            'user': {
                'userName': form_dict['name'],
                'phoneNumber':form_dict['phone']
            }
        }))

    return flask.send_from_directory('static', 'confirmation.html')

@app.route("/")
def home():
    return flask.send_from_directory('static', 'index.html')

if __name__ == '__main__':
    client = mqtt.Client()
    client.connect('broker')
    client.loop_start()

    app.run(host='0.0.0.0')
