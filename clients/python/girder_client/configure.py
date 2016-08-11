import argparse
import os
import sys
import girder_client


def get_config(section, option):
    return girder_client.config.get(section, option)


def set_config(section, option, value):
    if not girder_client.config.has_section(section):
        girder_client.config.add_section(section)
    girder_client.config.set(section, option, value)
    write_config()


def write_config(fd=None):
    girder_client._safeMakedirs(girder_client.CONFIG_DIR)
    if fd is None:
        path = os.path.join(girder_client.CONFIG_DIR, 'girder-cli.conf')
        with open(path, 'w') as fd:
            girder_client.config.write(fd)
    else:
        girder_client.config.write(fd)


def rm_config(section, option):
    girder_client.config.remove_option(section, option)
    write_config()


def main():
    parser = argparse.ArgumentParser(
        description='Get and set configuration values for the client')
    parser.add_argument(
        '-c', required=False, default=None, dest='config',
        help='The location of the config file.')
    subparsers = parser.add_subparsers(help='sub-command help', dest='cmd')

    get_parser = subparsers.add_parser('get', help='get a config value')
    set_parser = subparsers.add_parser('set', help='set a config value')
    rm_parser = subparsers.add_parser('rm', help='remove a config option')
    subparsers.add_parser('list', help='show all config values')

    get_parser.add_argument(
        'section', help='The section containing the option.')
    get_parser.add_argument('option', help='The option to retrieve.')

    set_parser.add_argument(
        'section', help='The section containing the option.')
    set_parser.add_argument('option', help='The option to set.')
    set_parser.add_argument('value', help='The value to set the option to.')

    rm_parser.add_argument(
        'section', help='The section containing the option to remove.')
    rm_parser.add_argument('option', help='The option to remove.')

    args = parser.parse_args()

    if args.config is not None:
        if not os.path.isfile(args.config):
            print('The config file: "{}" does not exist.'.format(args.config),
                  'Falling back to defaults.')
        girder_client.config.read([args.config])
        if not girder_client.config.has_section('girder_client'):
            girder_client.config.add_section('girder_client')

    if args.cmd == 'get':
        print(get_config(args.section, args.option))
    elif args.cmd == 'set':
        set_config(args.section, args.option, args.value)
    elif args.cmd == 'list':
        write_config(sys.stdout)
    elif args.cmd == 'rm':
        rm_config(args.section, args.option)

if __name__ == '__main__':
    main()  # pragma: no cover
