import os
import time

from waggle.plugin import Plugin

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

def get_proc_stat(fd, keys, print_mode):

    with Plugin() as plugin:
        e = time.time()

        fd.seek(0)

        cpu_keys = keys - {'ctxt', 'intr'}
        cpu_line = fd.readline().split()
        for key in cpu_keys:
            topic = f'perf.proc.stat.{key}'
            value = cpu_line[cpu_idx_dict[key]]

            if print_mode:
                print(topic, value)
            else:
                plugin.publish(topic, value)

        for core_id in range(os.cpu_count()):
            core_line = fd.readline().split()
            for key in cpu_keys:
                topic = f'perf.proc.stat.cpu{core_id}.{key}'
                value = core_line[cpu_idx_dict[key]]
                
                if print_mode:
                    print(topic, value)
                else:
                    plugin.publish(f'perf.proc.stat.cpu{core_id}.{key}', core_line[cpu_idx_dict[key]])

        intr_line = fd.readline().split()
        if 'intr' in keys:
            topic = 'perf.proc.stat.intr'
            value = intr_line[1]

            if print_mode:
                print(topic, value)
            else:
                plugin.publish(topic, value)

        ctxt_line = fd.readline().split()
        if 'ctxt' in keys:
            topic = 'perf.proc.stat.ctxt'
            value = ctxt_line[1]

            if print_mode:
                print(topic, value)
            else:
                plugin.publish(topic, value)
