import os
import time
from collections import deque

cpu_idx_dict = {
    'user': 1,
    'nice': 2,
    'system': 3,
    'idle': 4,
    'iowait': 5,
    'irq': 6,
    'softirq': 7,
    'steal': 8
}


def update_rates(topic, value, rates, interval, period):
    if topic not in rates:
        rates[topic] = deque([])

    queue = rates[topic]
    queue.appendleft(value)

    if len(queue) > period:
        tmp = queue.pop()
        return (value - tmp) / period 
    else:
        return (value - queue[-1]) / len(queue)

def process(topic, value, command, row):
    command(topic, value)
    row[topic] = value

def get_proc_stat(fd, keys, context):
    
    interval = context['interval']
    aroc_period = context['aroc_period']
    rates = context['rates']
    command = context['command']
    row = context['row']

    fd.seek(0)
    cpu_keys = keys - {'ctxt', 'intr'}
    cpu_line = fd.readline().split()
    for key in cpu_keys:
        topic = f'perf.proc.stat.{key}'
        value = int(cpu_line[cpu_idx_dict[key]])
        rate = update_rates(topic, value, rates, interval, aroc_period) 
        process(topic, rate, command, row)

    for core_id in range(os.cpu_count()):
        core_line = fd.readline().split()
        for key in cpu_keys:
            topic = f'perf.proc.stat.cpu{core_id}.{key}'
            value = int(core_line[cpu_idx_dict[key]])
            rate = update_rates(topic, value, rates, interval, aroc_period) 
            process(topic, rate, command, row)
            
    intr_line = fd.readline().split()
    if 'intr' in keys:
        topic = 'perf.proc.stat.intr'
        value = int(intr_line[1])
        rate = update_rates(topic, value, rates, interval, aroc_period) 
        process(topic, rate, command, row)

    ctxt_line = fd.readline().split()
    if 'ctxt' in keys:
        topic = 'perf.proc.stat.ctxt'
        value = int(ctxt_line[1])
        rate = update_rates(topic, value, rates, interval, aroc_period) 
        process(topic, rate, command, row)
