import os
import uuid

from django.core.wsgi import get_wsgi_application

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_prod")

# OTEL_RESOURCE_ATTRIBUTES = {
#     "service.instance.id": str(uuid.uuid1()),
#     "environment": "local"
# }

# trace.set_tracer_provider(TracerProvider(resource=Resource.create(OTEL_RESOURCE_ATTRIBUTES)))
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(
    # OTLPSpanExporter(endpoint="https://otlp.eu01.nr-data.net:4317", headers={"api-key": "eu01xx69eb42136d50c5b476e604f595FFFFNRAL"})
    OTLPSpanExporter()
))
# trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

application = get_wsgi_application()
