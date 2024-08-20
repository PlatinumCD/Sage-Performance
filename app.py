import csv
import time
import math
import argparse

from fsparser import cpu
from waggle.plugin import Plugin

proc_stat_modules = [ 'proc:stat:' + i for i in [
    'user', 'nice', 'system', 'idle', 'iowait',
    'irq', 'softirq', 'steal', 'intr', 'ctxt']
]

sys_bus_i2c_modules = [
     'sys:bus:energy'
]

proc_memstat_modules = ['proc:memstat:' + i for i in [
    'total', 'free', 'available',
    'buffers', 'cached', 'swap_cached',
    'active', 'inactive', 'active_anon',
    'inactive_anon', 'active_file', 'inactive_file',
    'swap_total', 'swap_free', 'dirty',
    'writeback', 'anon_pages', 'mapped',
    'shmem', 'slab', 's_reclaimable',
    's_unreclaim', 'kernel_stack', 'page_tables']
]

def build_commands(options):

    modules = {} 
    for option in options:

        split_options = option.split(':')
        if len(split_options) != 3:
            continue
        
        group, subgroup, key = split_options 

        # Proc Group
        if group == 'proc':
            if 'proc' not in modules:
                modules['proc'] = {}

            # CPU Stat Subgroup
            if subgroup == 'stat':
                if 'stat' not in modules['proc']:
                    modules['proc']['stat'] = { 
                        'func': cpu.get_proc_stat, 
                        'file': '/proc/stat', 
                        'keys': []
                    }

            # Memory Usage Subgroup
            if subgroup == 'memstat':
                if 'memstat' not in modules['proc']:
                    modules['proc'] = { 
                        'func': None, #mem.get_proc_memstat, 
                        'file': '/proc/memstat',
                        'keys': []
                    }

        # Sys Group
        if group == 'sys':
            if 'sys' not in modules:
                modules['sys'] = {}

            # System Bus Subgroup
            if subgroup == 'bus':
                if 'bus' not in modules['sys']:
                    modules['sys']['bus'] = {
                        'func': None,
                        'file': None,
                        'key': []
                    }

        # Add keys
        modules[group][subgroup]['keys'].append(key)

    # Convert nested dictionary into commands list
    commands = []
    for group, submodules in modules.items():
        for subgroup, command in submodules.items():
            cmd_func = command['func']
            cmd_fd = open(command['file'])
            cmd_keys = set(command['keys'])
            commands.append((cmd_func, cmd_fd, cmd_keys))

    return commands


def run(args, plugin):

    # Process Args
    interval = args.interval
    duration = args.duration 
    debug = args.debug
    aroc_period = args.aroc_period
    csv_name = args.csv

    # Convert interval to seconds
    if interval < 0:
        interval = 0
    else:
        interval = interval / 1000.0

    # Compute number of rounds
    if duration < 0:
        rounds = math.inf
    else:
        rounds = int(duration / interval)

    # Whether CSV mode is on
    if csv_name == '':
        csv_mode = False
    else:
        csv_mode = True

    # Create commands
    options = set([key for key, value in vars(args).items() if value is True])
    commands = build_commands(options)

    if debug:
        process_command = print
    else:
        process_command = plugin.publish

    context = {
        'interval': interval,
        'aroc_period':aroc_period,
        'rates': {},
        'command': process_command,
        'row': {}
    }

    # Run data collection
    data = {}
    while rounds:
        for func, fd, params in commands:
            func(fd, params, context)

        if csv_mode:
            for key, value in context['row'].items():
                if key in data:
                    data[key].append(value)
                else:
                    data[key] = [value]

            context['row'] = {}

        time.sleep(interval)
        rounds -= 1


    # Get the keys (column names)
    keys = data.keys()

    # Open a CSV file for writing
    with open(csv_name, 'w', newline='') as output_file:
        dict_writer = csv.writer(output_file)

        # Write the header
        dict_writer.writerow(keys)

        # Write the rows
        rows = zip(*data.values())
        dict_writer.writerows(rows)

    # Close files
    for _, fd, _ in commands:
        fd.close()
    
    return

def add_arguments(modules, parser, group_name):
    group = parser.add_argument_group(group_name)
    for key in modules:
        group.add_argument( f'--{key}', dest=key, action='store_true', default=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '--interval', dest='interval',
        action='store', default=1000, type=int,
        help='Interval between data collection (milliseconds)')
    parser.add_argument(
        '--duration', dest='duration',
        action='store', default=60, type=int,
        help='Number of seconds to capture data')
    parser.add_argument(
        '--debug', dest='debug',
        action='store_true', default=False,
        help='Print data instead of publish data')
    parser.add_argument(
        '--aroc-period', dest='aroc_period',
        action='store', default=3, type=int,
        help='Average rate of change period')
    parser.add_argument(
        '--csv', dest='csv',
        action='store', default='', type=str,
        help='Name of the csv to create')

    add_arguments(proc_stat_modules, parser, '/proc/stat')
    add_arguments(sys_bus_i2c_modules, parser, '/sys/bus/i2c')
    add_arguments(proc_memstat_modules, parser, '/proc/memstat')
    args = parser.parse_args()
   
    with Plugin() as plugin:
        run(args, plugin)
