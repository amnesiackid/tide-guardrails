"""Package init.

Runs before any guard module is imported (importing ``tide_guardrails.pipeline``
executes this first), so it is the one place to quiet third-party noise and fix
the console encoding no matter which entry point is used.
"""
import logging
import os
import sys
import threading
import warnings

threading.stack_size(16 * 1024 * 1024)

# The Guardrails Hub telemetry sink is contacted on every validate(); offline it
# retries and floods the console. Must be set before guardrails builds its tracer.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

# transformers logs "Device set to use cpu" for every local pipeline; it resets
# its own logger level on import, so only its env var sticks.
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

# presidio registers es/it/pl recognizers that our en-only registry rejects, one
# WARNING each per DetectPII instance; the otel exporter logs export retries.
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

# Windows consoles default to a legacy codepage (gbk here), so printing the
# German or Chinese test messages raises UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")
