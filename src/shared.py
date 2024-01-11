import os
import socket


def is_service_ready(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.error, socket.timeout):
        return False


def is_zipkin_ready():
    return is_service_ready(os.environ.get("ZIPKIN_HOST", "localhost"), int(os.environ.get("ZIPKIN_PORT", "9411")), 1)


def is_upstream_ready():
    return is_service_ready(os.environ.get("UPSTREAM_MQTT_HOST", "localhost"), int(os.environ.get("UPSTREAM_MQTT_PORT", "1883")), 1)


def is_downstream_ready():
    return is_service_ready(os.environ.get("DOWNSTREAM_MQTT_HOST", "localhost"), int(os.environ.get("DOWNSTREAM_MQTT_PORT", "1883")), 1)
