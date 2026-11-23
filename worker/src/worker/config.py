import os
import time

import pika

QUEUE_NAME = os.getenv("QUEUE_NAME", "jobs")
DEAD_LETTER_QUEUE = f"{QUEUE_NAME}.dead-letter"


def amqp_url() -> str:
    url = os.getenv("AMQP_URL")
    if not url:
        raise SystemExit("AMQP_URL is not set, e.g. amqp://user:pass@rabbitmq:5672/%2F")
    return url


def connect(retries: int = 30, delay: float = 2.0) -> pika.BlockingConnection:
    """Connect to RabbitMQ, retrying while the broker starts up."""
    params = pika.URLParameters(amqp_url())
    params.heartbeat = 30
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError as exc:
            last_error = exc
            time.sleep(delay)
    raise SystemExit(f"could not connect to RabbitMQ: {last_error}")


def declare_queues(channel) -> None:
    """Durable work queue; rejected (poison) messages go to a dead-letter queue."""
    channel.queue_declare(queue=DEAD_LETTER_QUEUE, durable=True)
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": DEAD_LETTER_QUEUE,
        },
    )
