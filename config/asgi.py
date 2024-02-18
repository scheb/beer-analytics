import os

from django.core.asgi import get_asgi_application
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.dbapi import trace_integration
import MySQLdb

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_prod")

# Open Telemetry
DjangoInstrumentor().instrument(is_sql_commentor_enabled=True)
trace_integration(MySQLdb, "connect", "mysql")

application = get_asgi_application()
application = OpenTelemetryMiddleware(application)
