#!/usr/bin/env python3

import asyncio

import django
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.http import JsonResponse
from django.urls import path


if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='benchmark-secret-key-not-for-production',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        USE_TZ=True,
        MIDDLEWARE=[],
        INSTALLED_APPS=[],
        LOGGING={
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'null': {
                    'class': 'logging.NullHandler',
                },
            },
            'root': {
                'handlers': ['null'],
            },
        },
    )

django.setup()


async def _yield_once() -> int:
    await asyncio.sleep(0)
    return 1


async def raw_async(request):
    return JsonResponse({
        'framework': 'django',
        'mode': 'raw_async',
        'value': 1,
    })


async def yield_once(request):
    value = await _yield_once()
    return JsonResponse({
        'framework': 'django',
        'mode': 'yield_once',
        'value': value,
    })


async def fanout_async(request):
    results = await asyncio.gather(_yield_once(), _yield_once(), _yield_once())
    return JsonResponse({
        'framework': 'django',
        'mode': 'fanout_async',
        'value': sum(results),
    })


async def chain_async(request, steps: int):
    total = 0
    for _ in range(steps):
        total += await _yield_once()
    return JsonResponse({
        'framework': 'django',
        'mode': 'chain_async',
        'steps': steps,
        'value': total,
    })


urlpatterns = [
    path('async/raw', raw_async, name='raw_async'),
    path('async/yield-once', yield_once, name='yield_once'),
    path('async/fanout', fanout_async, name='fanout_async'),
    path('async/chain/<int:steps>', chain_async, name='chain_async'),
]


application = get_asgi_application()