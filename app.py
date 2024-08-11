import time
import argparse

from fsparser import cpu

from waggle.plugin import Plugin

proc_stat_modules = [ 
     'proc:stat:user', 'proc:stat:nice', 'proc:stat:system', 
     'proc:stat:idle', 'proc:stat:iowait', 'proc:stat:irq', 
     'proc:stat:softirq', 'proc:stat:steal', 'proc:stat:intr',
     'proc:stat:ctxt' 
]

sys_bus_i2c_modules = [
     'sys:bus:energy'
]

proc_memstat_modules = [
    'proc:memstat:total', 'proc:memstat:free', 'proc:memstat:available',
    'proc:memstat:buffers', 'proc:memstat:cached', 'proc:memstat:swap_cached',
    'proc:memstat:active', 'proc:memstat:inactive', 'proc:memstat:active_anon',
    'proc:memstat:inactive_anon', 'proc:memstat:active_file', 'proc:memstat:inactive_file',
    'proc:memstat:swap_total', 'proc:memstat:swap_free', 'proc:memstat:dirty',
    'proc:memstat:writeback', 'proc:memstat:anon_pages', 'proc:memstat:mapped',
    'proc:memstat:shmem', 'proc:memstat:slab', 'proc:memstat:s_reclaimable',
    'proc:memstat:s_unreclaim', 'proc:memstat:kernel_stack', 'proc:memstat:page_tables'
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


def run(args):

    print(args)
    seconds = 0 if args.interval < 0 else args.interval / 1000.0
    rounds = iter(int, 1) if args.rounds < 0 else range(args.rounds)
    print_mode = args.print_mode
    options = set([key for key, value in vars(args).items() if value is True])

    commands = build_commands(options)

    with Plugin() as plugin:

        if print_mode:
            output_method = print
        else:
            output_method = plugin.publish

        # Run data collection
        for _ in rounds:
            for func, fd, params in commands:
                func(fd, params, output_method)
            time.sleep(seconds)

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
        '--rounds', dest='rounds',
        action='store', default=5, type=int,
        help='Number of data collection rounds')
    parser.add_argument(
        '--print_mode', dest='print_mode',
        action='store_true', default=False,
        help='Print data instead of publish data')

    add_arguments(proc_stat_modules, parser, '/proc/stat')
    add_arguments(sys_bus_i2c_modules, parser, '/sys/bus/i2c')
    add_arguments(proc_memstat_modules, parser, '/proc/memstat')

    run(parser.parse_args())
