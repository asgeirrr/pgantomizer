import argparse
import logging
import os
import subprocess
import sys

import yaml


def dump_db(schema_path, dump_path, *db_args):
    schema = yaml.load(open(schema_path))
    cmd = 'pg_dump -Fc -Z 9 {args} {tables} -f {filename}'.format(
        args='-d {} -U {} -h {} -p {} '.format(
            *(db_args or [os.environ.get(var) for var in ['DB_DEFAULT_NAME', 'DB_DEFAULT_USER',
                                                          'DB_DEFAULT_SERVICE', 'DB_DEFAULT_PORT']])),
        tables=' '.join('-t {}'.format(table) for table in schema),
        filename=dump_path
    )
    logging.debug('Dumping DB with following command: {}'.format(cmd))
    subprocess.run(cmd, shell=True)


def main():
    parser = argparse.ArgumentParser(description='Dump tables specified in YAML config file from production DB '
                                                 'for later anonymization.',
                                     epilog='Compressed Postgres format is used. See README.md for details.')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--schema',  help='YAML config file with tables to dump', default='./schema.yaml')
    parser.add_argument('--dump-file',  help='path to the file where to dump the DB', default='to_anonymize.sql')
    parser.add_argument('--db-name',  help='name of the database to dump')
    parser.add_argument('--user', help='name of the Postgres user with access to the database')
    parser.add_argument('--password', help='password of the Postgres user with access to the database', default='')
    parser.add_argument('--host', help='host where the DB is running', default='localhost')
    parser.add_argument('--port', help='port where the DB is running', default='5432')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s")

    if not os.path.isfile(args.schema):
        sys.exit('File with schema "{}" does not exist.'.format(args.schema))

    dump_db(
        args.schema,
        args.dump_file,
        *([args.db_name, args.user, args.host, args.port]
          if args.db_name and args.user else [])
    )

if __name__ == '__main__':
    main()
