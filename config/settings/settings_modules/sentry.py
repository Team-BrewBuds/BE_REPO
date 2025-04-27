import django
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from config.settings._base import env

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(
            transaction_style="url",
            middleware_spans=True,
            signals_spans=True,
            signals_denylist=[
                django.db.models.signals.pre_init,
                django.db.models.signals.post_init,
            ],
            cache_spans=True,
        ),
    ],
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)
