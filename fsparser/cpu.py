import os
import time

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

def get_proc_stat(fd, keys, publish, print_mode):
    e = time.time()

    fd.seek(0)

    cpu_keys = keys - {'ctxt', 'intr'}
    cpu_line = fd.readline().split()
    for key in cpu_keys:
        if print_mode:
            print(f'perf.proc.stat.{key}:', cpu_line[cpu_idx_dict[key]])
        else:
            publish(f'perf.proc.stat.{key}:', cpu_line[cpu_idx_dict[key]], timestamp=e)

    for core_id in range(os.cpu_count()):
        core_line = fd.readline().split()
        for key in cpu_keys:
            if print_mode:
                print(f'perf.proc.stat.cpu{core_id}.{key}:', core_line[cpu_idx_dict[key]])
            else:
                publish(f'perf.proc.stat.cpu{core_id}.{key}:', core_line[cpu_idx_dict[key]], timestamp=e)

    intr_line = fd.readline().split()
    if 'intr' in keys:
        if print_mode:
            print(f'perf.proc.stat.intr:', intr_line[1])
        else:
            publish(f'perf.proc.stat.intr:', intr_line[1], timestamp=e)

    ctxt_line = fd.readline().split()
    if 'ctxt' in keys:
        if print_mode:
            print(f'perf.proc.stat.ctxt:', ctxt_line[1])
        else:
            publish(f'perf.proc.stat.ctxt:', ctxt_line[1], timestamp=e)
