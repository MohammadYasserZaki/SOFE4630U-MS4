import glob                             # for searching for json file
import os                               # for setting and reading environment variables
from google.cloud import pubsub_v1      # pip install google-cloud-pubsub
import time                             # for sleep function
import json                             # to deal with json objects
import sys                              # for exit function


# Search the current directory for the JSON file (including the Google Pub/Sub credential)
# to set the GOOGLE_APPLICATION_CREDENTIALS environment variable.
files = glob.glob("*.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = files[0]

# Get the environment variables to set the corresponding variables
project_id = os.environ["GCP_PROJECT"]
subscription_id = os.environ["CONVERT_SUB_ID"]
topic_name = os.environ["TOPIC_NAME"]

debug = False  # change to True for debugging
if "Debug" in os.environ:  # or define it as an environment variable
    debug = True
if debug:
    print(files[0])
    print(project_id)
    print(subscription_id)
    print(topic_name)

# create a publisher and get the topic path for the publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

# The callback function for handling received messages
def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    # Make sure that the global variables are accessed from within the function.
    global publisher, topic_path

    # get the message content
    message_data = json.loads(message.data)

    if debug:
        print(f"Received {message_data}.")

    # Convert pressure from kPa to psi: P(psi) = P(kPa) / 6.895
    pressure_kpa = message_data.get('pressure_kpa')
    pressure_psi = pressure_kpa / 6.895

    # Convert temperature from Celsius to Fahrenheit: T(F) = T(C) * 1.8 + 32
    temperature_celsius = message_data.get('temperature_celsius')
    temperature_fahrenheit = temperature_celsius * 1.8 + 32

    # Create the converted message
    converted_data = {
        'meter_id': message_data.get('meter_id'),
        'timestamp': message_data.get('timestamp'),
        'pressure_psi': round(pressure_psi, 2),
        'temperature_fahrenheit': round(temperature_fahrenheit, 2)
    }

    if debug:
        print(f"Converted reading: {converted_data}")

    # Publish the converted data
    future = publisher.publish(
        topic_path,
        json.dumps(converted_data).encode('utf-8'),
        function="converted_reading"
    )

    # Report to Google Pub/Sub the successful processing of the received message
    message.ack()

# create a subscriber to the subscription for the project using the subscription_id
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)
sub_filter = 'attributes.function="filtered_reading"'  # the condition used for filtering the messages to be received

print(f"ConvertReading service listening for messages on {subscription_path}..\n")

with subscriber:
    # Create a subscription with the given ID and filter for the first time, if not already existed
    try:
        subscription = subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path, "filter": sub_filter}
        )
        print(f"Created new subscription: {subscription_path}")
    except Exception as e:
        if debug:
            print(f"Subscription already exists or error: {e}")
        pass

    # Now, the subscription is already existing or has been created.
    # The callback function will be called for each message that matches the filter from the topic.
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
