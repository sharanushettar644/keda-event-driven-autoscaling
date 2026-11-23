"""Queue consumer. KEDA scales the number of these pods with queue depth,
including down to zero when the queue is empty."""

import logging
import os
import signal
import socket

from worker.config import QUEUE_NAME, connect, declare_queues
from worker.messages import InvalidMessage, process

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer")

POD = os.getenv("HOSTNAME", socket.gethostname())


def main() -> None:
    connection = connect()
    channel = connection.channel()
    declare_queues(channel)
    # One unacknowledged message per pod: work is spread evenly across replicas
    # and a pod being scaled in never holds a backlog of messages.
    channel.basic_qos(prefetch_count=1)

    processed = 0

    def on_message(ch, method, _properties, body):
        nonlocal processed
        try:
            job = process(body)
        except InvalidMessage as exc:
            log.warning("rejecting poison message: %s", exc)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        processed += 1
        ch.basic_ack(delivery_tag=method.delivery_tag)
        log.info("pod=%s processed job=%s total=%s", POD, job.id, processed)

    # Graceful scale-in: on SIGTERM stop taking new messages; the message in
    # flight finishes and is acked before the process exits.
    def shutdown(signum, _frame):
        log.info("received signal %s, finishing current message and exiting", signum)
        connection.add_callback_threadsafe(channel.stop_consuming)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)
    log.info("pod=%s waiting for messages on '%s'", POD, QUEUE_NAME)
    channel.start_consuming()
    connection.close()
    log.info("pod=%s stopped after processing %s messages", POD, processed)


if __name__ == "__main__":
    main()
