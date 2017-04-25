#!/usr/bin/python
from multiprocessing import cpu_count
from os import environ

bind = '0.0.0.0:' + environ.get('PORT', '8051')
max_requests = 1000
workers = cpu_count()
