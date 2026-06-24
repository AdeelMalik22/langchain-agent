from datetime import datetime
import json
import logging

logger = logging.getLogger("kafka_producer")
logging.basicConfig(level=logging.INFO)

def send_kafka_log(event: str, data: dict):
    log = {
        "event": event,
        "data": data,
        "time": datetime.now().isoformat(),
    }
    # Mock log output instead of sending to a Kafka broker
    logger.info(f"[MOCK KAFKA LOG] {json.dumps(log)}")
