"""Publishes a burst of jobs to the queue. Run it as a Kubernetes Job to
generate load and watch KEDA scale the consumers."""

import logging
import os

import pika

from worker.config import QUEUE_NAME, connect, declare_queues
from worker.messages import build_jobs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("producer")


def main() -> None:
    count = int(os.getenv("MESSAGE_COUNT", "100"))
    work_ms = int(os.getenv("WORK_MS", "1000"))

    connection = connect()
    channel = connection.channel()
    declare_queues(channel)
    channel.confirm_delivery()

    persistent = pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
    for job in build_jobs(count, work_ms):
        channel.basic_publish(
            exchange="", routing_key=QUEUE_NAME, body=job.to_bytes(), properties=persistent
        )

    connection.close()
    log.info("published %s jobs of %sms each to '%s'", count, work_ms, QUEUE_NAME)


if __name__ == "__main__":
    main()
