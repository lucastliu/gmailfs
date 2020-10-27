from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1


import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "CREDENTIAL_PATH"
# TODO(developer)
project_id = "crucial-matter-292203"
subscription_id = "sub_one"
# Number of seconds the subscriber should listen for messages
timeout = 5.0

subscriber = pubsub_v1.SubscriberClient()
# The `subscription_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message):
    print(f"Received {message}.")
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

# Wrap subscriber in a 'with' block to automatically call close() when done.
#with subscriber:
try:
    # When `timeout` is not set, result() will block indefinitely,
    # unless an exception is encountered first.
    streaming_pull_future.result()
except TimeoutError:
    streaming_pull_future.cancel()