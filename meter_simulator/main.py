import glob                             # for searching for json file
import os                               # for setting and reading environment variables
from google.cloud import pubsub_v1      # pip install google-cloud-pubsub
import time                             # for sleep function
import json                             # to deal with json objects
import random                           # to generate random values

# Search the current directory for the JSON file (including the Google Pub/Sub credential)
# to set the GOOGLE_APPLICATION_CREDENTIALS environment variable.
files = glob.glob("*.json")
if len(files) > 0:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = files[0]

# Set the project ID and topic name
project_id = ""  # TODO: Set your project ID here
topic_name = "smartmeter"

# Let the user enter the meter ID
meter_id = input("Please enter the meter ID (string): ")

debug = False  # change to True for debugging
if debug:
    print(files[0])
    print(meter_id)
    print(project_id)
    print(topic_name)

# create a publisher and get the topic path for the publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

print(f"Smart Meter Simulator started for meter: {meter_id}")
print(f"Publishing messages to {topic_path}..\n")

# Main loop to generate and send smart meter readings
reading_count = 0
while True:
    reading_count += 1

    # Randomly decide if this reading should have None values (10% chance)
    has_missing_data = random.random() < 0.1

    # Generate random smart meter reading
    if has_missing_data:
        # Generate reading with some None values
        pressure_kpa = None if random.random() < 0.5 else round(random.uniform(95.0, 105.0), 2)
        temperature_celsius = None if random.random() < 0.5 else round(random.uniform(15.0, 30.0), 2)
    else:
        # Generate valid reading
        pressure_kpa = round(random.uniform(95.0, 105.0), 2)
        temperature_celsius = round(random.uniform(15.0, 30.0), 2)

    value = {
        'meter_id': meter_id,
        'timestamp': int(1000 * time.time()),
        'pressure_kpa': pressure_kpa,
        'temperature_celsius': temperature_celsius
    }

    # Publish the reading message
    future = publisher.publish(
        topic_path,
        json.dumps(value).encode('utf-8'),
        function="raw_reading"
    )

    status = "VALID" if not has_missing_data else "INVALID (contains None)"
    print(f"Reading #{reading_count} sent [{status}]: {value}")

    # Send a new reading every 2 seconds
    time.sleep(2)
