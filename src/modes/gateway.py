import json
import os
from time import sleep
import paho.mqtt.client as mqtt
import paho.mqtt.properties as props
from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from paho.mqtt.packettypes import PacketTypes
from shared import is_zipkin_ready, is_upstream_ready, is_downstream_ready


def wait_dependencies():
    while is_zipkin_ready() is False:
        print("Waiting for zipkin...")
        sleep(1)
    while is_upstream_ready() is False:
        print("Waiting for upstream...")
        sleep(1)
    while is_downstream_ready() is False:
        print("Waiting for downstream...")
        sleep(1)


def gateway():
    wait_dependencies()
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

    def on_connect(client, userdata, flags, rc, properties=None):
        client.subscribe("#")
        if rc == 0:
            print("Bağlantı başarılı.")
        else:
            print(f"Bağlantı hatası, Kod: {rc}")

    def on_message_upstream(client, userdata, msg):
        service_name = os.environ.get("SERVICE_NAME", "default-service")
        user_properties = None
        if hasattr(msg, 'properties'):
            properties = msg.properties
            if hasattr(properties, 'UserProperty'):
                user_properties = dict(properties.UserProperty)
                keys = user_properties.keys()
                if ("upstream_client_id" in keys and user_properties["upstream_client_id"] == os.environ.get("UPSTREAM_MQTT_CLIENT_ID", "client-default"))\
                        and ("downstream_client_id" in keys and user_properties["downstream_client_id"] == os.environ.get("DOWNSTREAM_MQTT_CLIENT_ID", "client-default")):
                    return
        topic = msg.topic
        data = msg.payload.decode()
        stream_properties = props.Properties(PacketTypes.PUBLISH)
        if user_properties is not None:
            for key in user_properties:
                stream_properties.UserProperty = (key, user_properties[key])
        stream_properties.UserProperty = ("upstream_client_id", os.environ.get("UPSTREAM_MQTT_CLIENT_ID", "client-default"))
        stream_properties.UserProperty = ("downstream_client_id", os.environ.get("DOWNSTREAM_MQTT_CLIENT_ID", "client-default"))
        stream_ok = False
        if "trace_carrier" in user_properties:
            if bool(os.environ.get("TRACING", "true")) is True:
                prop = TraceContextTextMapPropagator()
                carrier = json.loads(user_properties["trace_carrier"])
                ctx = prop.extract(carrier=carrier)
                with tracer.start_as_current_span(service_name, context=ctx, kind=SpanKind.PRODUCER):
                    stream_ok = True
                    downstream_client.publish(topic, payload=data, qos=1, properties=stream_properties)
        if stream_ok is False:
            downstream_client.publish(topic, payload=data, qos=1, properties=stream_properties)
        print("Publish: " + str(data) + " to topic: " + topic)

    def on_message_downstream(client, userdata, msg):
        user_properties = None
        if hasattr(msg, 'properties'):
            properties = msg.properties
            if hasattr(properties, 'UserProperty'):
                user_properties = dict(properties.UserProperty)
                keys = user_properties.keys()
                if ("upstream_client_id" in keys and user_properties["upstream_client_id"] == os.environ.get("UPSTREAM_MQTT_CLIENT_ID", "client-default"))\
                        and ("downstream_client_id" in keys and user_properties["downstream_client_id"] == os.environ.get("DOWNSTREAM_MQTT_CLIENT_ID", "client-default")):
                    return
        topic = msg.topic
        data = msg.payload.decode()
        stream_properties = props.Properties(PacketTypes.PUBLISH)
        if user_properties is not None:
            for key in user_properties:
                stream_properties.UserProperty = (key, user_properties[key])
        stream_properties.UserProperty = ("upstream_client_id", os.environ.get("UPSTREAM_MQTT_CLIENT_ID", "client-default"))
        stream_properties.UserProperty = ("downstream_client_id", os.environ.get("DOWNSTREAM_MQTT_CLIENT_ID", "client-default"))
        stream_ok = False
        if "trace_carrier" in user_properties:
            if bool(os.environ.get("TRACING", "true")) is True:
                prop = TraceContextTextMapPropagator()
                carrier = json.loads(user_properties["trace_carrier"])
                ctx = prop.extract(carrier=carrier)
                with tracer.start_as_current_span(service_name, context=ctx, kind=SpanKind.PRODUCER):
                    stream_ok = True
                    upstream_client.publish(topic, payload=data, qos=1, properties=stream_properties)
        if stream_ok is False:
            upstream_client.publish(topic, payload=data, qos=1, properties=stream_properties)
        print("Publish: " + str(data) + " to topic: " + topic)

    upstream_broker_address = os.environ.get("UPSTREAM_MQTT_HOST", "localhost")
    upstream_port = int(os.environ.get("UPSTREAM_MQTT_PORT", "1883"))
    upstream_username = os.environ.get("UPSTREAM_MQTT_USERNAME", "")
    upstream_password = os.environ.get("UPSTREAM_MQTT_PASSWORD", "")
    downstream_broker_address = os.environ.get("DOWNSTREAM_MQTT_HOST", "localhost")
    downstream_port = int(os.environ.get("DOWNSTREAM_MQTT_PORT", "1883"))
    downstream_username = os.environ.get("DOWNSTREAM_MQTT_USERNAME", "")
    downstream_password = os.environ.get("DOWNSTREAM_MQTT_PASSWORD", "")

    print("Zinkin: " + os.environ.get("ZIPKIN_HOST", "localhost") + ":" + os.environ.get("ZIPKIN_PORT", "9411") + "/api/v2/spans")
    print("Upstream MQTT: " + upstream_broker_address + ":" + str(upstream_port))
    print("Downstream MQTT: " + downstream_broker_address + ":" + str(downstream_port))

    upstream_client = mqtt.Client(os.environ.get("UPSTREAM_MQTT_CLIENT_ID", "client-default"), protocol=mqtt.MQTTv5)
    upstream_client.username_pw_set(upstream_username, upstream_password)
    upstream_client.on_connect = on_connect
    upstream_client.on_message = on_message_upstream
    upstream_client.connect(upstream_broker_address, upstream_port, 60)

    downstream_client = mqtt.Client(os.environ.get("DOWNSTREAM_MQTT_CLIENT_ID", "client-default"), protocol=mqtt.MQTTv5)
    downstream_client.username_pw_set(downstream_username, downstream_password)
    downstream_client.on_connect = on_connect
    downstream_client.on_message = on_message_downstream
    downstream_client.connect(downstream_broker_address, downstream_port, 60)

    try:
        upstream_client.subscribe("#")
        downstream_client.subscribe("#")
        upstream_client.loop_start()
        downstream_client.loop_start()
        while True:
            sleep(1)
    finally:
        upstream_client.loop_stop()
        upstream_client.disconnect()
        downstream_client.loop_stop()
        downstream_client.disconnect()
