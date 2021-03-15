import os
from celery import Celery

BROKER = os.environ.get('BROKER', 'amqp://localhost:5672')


def make_celery(app_name=__name__):
    return Celery(app_name, backend='rpc://', broker=BROKER)


celery = make_celery()
