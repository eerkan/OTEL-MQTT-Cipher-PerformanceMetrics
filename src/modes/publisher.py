import json
import os
import socket
from time import sleep
import paho.mqtt.client as mqtt
import paho.mqtt.properties as props
from data_generator import generate_random_data_by_data_type, total_exp_data_size
import uuid
from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from paho.mqtt.packettypes import PacketTypes
from cipher import encrypt
from profile import my_simple_profile
from shared import is_zipkin_ready, is_upstream_ready


def wait_dependencies():
    while is_zipkin_ready() is False:
        print("Waiting for zipkin...")
        sleep(1)
    while is_upstream_ready() is False:
        print("Waiting for upstream...")
        sleep(1)


def publisher():
    wait_dependencies()
    if bool(os.environ.get("TRACING", "true")) is True:
        service_name = os.environ.get("SERVICE_NAME", "default-service")
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

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Bağlantı başarılı.")
        else:
            print(f"Bağlantı hatası, Kod: {rc}")

    upstream_broker_address = os.environ.get("UPSTREAM_MQTT_HOST", "localhost")
    upstream_port = int(os.environ.get("UPSTREAM_MQTT_PORT", "1883"))
    upstream_username = os.environ.get("UPSTREAM_MQTT_USERNAME", "")
    upstream_password = os.environ.get("UPSTREAM_MQTT_PASSWORD", "")

    print("Zinkin: " + os.environ.get("ZIPKIN_HOST", "localhost") + ":" + os.environ.get("ZIPKIN_PORT", "9411") + "/api/v2/spans")
    print("Upstream MQTT: " + upstream_broker_address + ":" + str(upstream_port))

    upstream_client = mqtt.Client(os.environ.get("UPSTREAM_MQTT_CLIENT_ID", "client-default"), protocol=mqtt.MQTTv5)
    upstream_client.username_pw_set(upstream_username, upstream_password)

    upstream_client.on_connect = on_connect

    upstream_client.connect(upstream_broker_address, upstream_port, 60)

    @my_simple_profile()
    def publisher_encrypt(raw_data):
        try:
            data = str(raw_data).encode("latin1")
            data = encrypt(data, cipher_payload)
            data = data.decode("latin1")
        except:
            print("EXCEPTION" * 1000)
            return raw_data
        return data

    try:
        upstream_client.loop_start()
        exp_key = os.environ.get("EXP_KEY", "").encode("latin1")
        total_exp = int(total_exp_data_size())
        topic = os.environ.get("UPSTREAM_PUBLISH_TOPIC", "default-topic")
        cipher_payload = json.loads(os.environ.get("CIPHER_PAYLOAD", "{}"))
        if "key" in cipher_payload:
            cipher_payload["key"] = cipher_payload["key"].encode("latin1")
        counter = 0
        while True:
            data = generate_random_data_by_data_type(counter)
            counter += 1
            if os.environ.get("RANDOM_DATA_TYPE", "") == "exp":
                cipher_payload = {
                    "algorithm": data["cipher"],
                    "key": exp_key
                }
                data = data["data"]
                print("Exp: " + str(counter) + " / " + str(total_exp))
                if counter >= total_exp:
                    break
            if data is not None:
                message_id = uuid.uuid4().hex
                carrier = {}
                stream_properties = props.Properties(PacketTypes.PUBLISH)
                stream_properties.UserProperty = ("message_id", message_id)
                stream_properties.UserProperty = ("publisher_name", service_name)
                if os.environ.get("RANDOM_DATA_TYPE", "") == "exp":
                    stream_properties.UserProperty = ("counter", str(counter - 1))
                is_publish = False
                if bool(os.environ.get("TRACING", "true")) is True:
                    prop = TraceContextTextMapPropagator()
                    with tracer.start_as_current_span(service_name, kind=SpanKind.PRODUCER) as span:
                        prop.inject(carrier=carrier)
                        stream_properties.UserProperty = ("trace_carrier", json.dumps(carrier))
                        is_publish = True
                        data = str(data)
                        raw_data_size = len(data)
                        with tracer.start_as_current_span("crypt") as crpyt_span:
                            data, peak_memory_usage, average_execution_time = publisher_encrypt(data)
                            encrypted_data_size = len(data)
                            cipher_payload_trace = cipher_payload.copy()
                            cipher_payload_trace["key"] = "********"
                            crpyt_span.set_attribute("cipher_payload", json.dumps(cipher_payload_trace))
                            crpyt_span.set_attribute("data", data)
                            crpyt_span.set_attribute("publisher_name", service_name)
                            crpyt_span.set_attribute("message_id", message_id)
                            crpyt_span.set_attribute("peak_memory_usage", peak_memory_usage)
                            crpyt_span.set_attribute("average_execution_time", average_execution_time)
                            crpyt_span.set_attribute("raw_data_size", raw_data_size)
                            crpyt_span.set_attribute("encrypted_data_size", encrypted_data_size)
                        upstream_client.publish(topic, payload=data, qos=1, properties=stream_properties)
                if is_publish is False:
                    data = publisher_encrypt(data)
                    upstream_client.publish(topic, payload=data, qos=1, properties=stream_properties)
                print("Publish: " + str(data) + " (id: " + message_id + ") to topic: " + topic)
            sleep(float(os.environ.get("RANDOM_DATA_INTERVAL", "1000")) / 1000.0)
    finally:
        upstream_client.loop_stop()
        upstream_client.disconnect()
