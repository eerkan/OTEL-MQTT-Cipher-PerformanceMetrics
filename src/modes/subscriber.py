import json
import os
from time import sleep
import paho.mqtt.client as mqtt
from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from cipher import decrypt
from profile import my_simple_profile
from data_generator import generate_exp_data
from shared import is_zipkin_ready, is_downstream_ready


def wait_dependencies():
    while is_zipkin_ready() is False:
        print("Waiting for zipkin...")
        sleep(1)
    while is_downstream_ready() is False:
        print("Waiting for downstream...")
        sleep(1)


def subscriber():
    wait_dependencies()
    exp_key = os.environ.get("EXP_KEY", "").encode("latin1")
    service_name = os.environ.get("SERVICE_NAME", "default-service")
    if bool(os.environ.get("TRACING", "true")) is True:
        resource = Resource(attributes={
            "service.name": os.environ.get("SERVICE_NAME", "default-service")
        })
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer = trace.get_tracer(__name__)
        zipkin_exporter = ZipkinExporter(
            endpoint= "http://" + os.environ.get("ZIPKIN_HOST", "localhost") + ":" + os.environ.get("ZIPKIN_PORT", "9411") + "/api/v2/spans",
        )
        span_processor = BatchSpanProcessor(zipkin_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

    @my_simple_profile()
    def subscriber_decrypt(raw_data, cipher_payload={}):
        try:
            data = str(raw_data).encode("latin1")
            data = decrypt(data, cipher_payload)
            data = data.decode("latin1")
        except:
            print("EXCEPTION" * 1000)
            return raw_data
        return data

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Bağlantı başarılı.")
        else:
            print(f"Bağlantı hatası, Kod: {rc}")

    def on_message(client, userdata, msg):
        message_id = None
        publisher_name = None
        cipher_payload = {}
        if hasattr(msg, 'properties'):
            properties = msg.properties
            if hasattr(properties, 'UserProperty'):
                user_properties = dict(properties.UserProperty)
                print(user_properties)
                if os.environ.get("RANDOM_DATA_TYPE", "") == "exp":
                    counter = int(user_properties["counter"])
                    cipher_data = generate_exp_data(counter, False)
                    cipher_payload = {
                        "algorithm": cipher_data["cipher"],
                        "key": exp_key
                    }
                if "message_id" in user_properties:
                    message_id = user_properties["message_id"]
                if "publisher_name" in user_properties:
                    publisher_name = user_properties["publisher_name"]
                if "key" not in cipher_payload:
                    cipher_payload = json.loads(os.environ.get(publisher_name.replace("-", "_").upper() + "_CIPHER_PAYLOAD", "{}"))
                    if "key" in cipher_payload:
                        cipher_payload["key"] = cipher_payload["key"].encode("latin1")
                data = msg.payload.decode()
                is_ok = False
                if "trace_carrier" in user_properties:
                    if bool(os.environ.get("TRACING", "true")) is True:
                        prop = TraceContextTextMapPropagator()
                        carrier = json.loads(user_properties["trace_carrier"])
                        ctx = prop.extract(carrier=carrier)
                        with tracer.start_as_current_span(service_name, context=ctx, kind=SpanKind.CONSUMER):
                            data = str(data)
                            raw_data_size = len(data)
                            is_ok = True
                            with tracer.start_as_current_span("decrypt") as crpyt_span:
                                data, peak_memory_usage, average_execution_time = subscriber_decrypt(data, cipher_payload)
                                decrypted_data_size = len(data)
                                cipher_payload_trace = cipher_payload.copy()
                                cipher_payload_trace["key"] = "********"
                                crpyt_span.set_attribute("cipher_payload", json.dumps(cipher_payload_trace))
                                crpyt_span.set_attribute("decrypted_data", data)
                                crpyt_span.set_attribute("publisher_name", service_name)
                                crpyt_span.set_attribute("message_id", message_id)
                                crpyt_span.set_attribute("peak_memory_usage", peak_memory_usage)
                                crpyt_span.set_attribute("average_execution_time", average_execution_time)
                                crpyt_span.set_attribute("raw_data_size", raw_data_size)
                                crpyt_span.set_attribute("decrypted_data_size", decrypted_data_size)
                                print(f"Message: {data} (id: " + message_id + ") from topic: " + msg.topic)
        if is_ok is False:
            data = subscriber_decrypt(data, cipher_payload)
            print(f"Message: {data} (id: " + message_id + ") from topic: " + msg.topic)

    downstream_broker_address = os.environ.get("DOWNSTREAM_MQTT_HOST", "localhost")
    downstream_port = int(os.environ.get("DOWNSTREAM_MQTT_PORT", "1883"))
    downstream_username = os.environ.get("DOWNSTREAM_MQTT_USERNAME", "")
    downstream_password = os.environ.get("DOWNSTREAM_MQTT_PASSWORD", "")

    print("Zinkin: " + os.environ.get("ZIPKIN_HOST", "localhost") + ":" + os.environ.get("ZIPKIN_PORT", "9411") + "/api/v2/spans")
    print("Downstream MQTT: " + downstream_broker_address + ":" + str(downstream_port))

    downstream_client = mqtt.Client(os.environ.get("DOWNSTREAM_MQTT_CLIENT_ID", "client-default"), protocol=mqtt.MQTTv5)
    downstream_client.username_pw_set(downstream_username, downstream_password)

    downstream_client.on_connect = on_connect
    downstream_client.on_message = on_message

    downstream_client.connect(downstream_broker_address, downstream_port, 60)

    try:
        topics_str = os.environ.get("DOWNSTREAM_SUBSCRIBE_TOPICS", "default-topic")
        topics = topics_str.split(",")
        for topic in topics:
            downstream_client.subscribe(topic)
        downstream_client.loop_start()
        while True:
            sleep(1)
    finally:
        downstream_client.loop_stop()
        downstream_client.disconnect()