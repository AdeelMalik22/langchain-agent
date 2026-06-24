# kafka_consumer.py

from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'user-events',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    group_id='log-consumers',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("Listening for user login events...")
for message in consumer:
    event = message.value
    print(f"Received event: {event}")

