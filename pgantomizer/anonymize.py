import argparse
import logging
import os
import subprocess
import sys

import psycopg2

import yaml

from .utils import get_in


DEFAULT_PK_COLUMN_NAME = 'id'

ANONYMIZE_DATA_TYPE = {
    'timestamp with time zone': "'1111-11-11 11:11:11.111111+00'",
    'date': "'1111-11-11'",
    'boolean': 'random() > 0.5',
    'integer': 'ceil(random() * 100)',
    'smallint': 'ceil(random() * 100)',
    'numeric': 'floor(random() * 10)',
    'character varying': lambda column, pk_name: "'{}_' || {}".format(column, pk_name),
    'text': lambda column, pk_name: "'{}_' || {}".format(column, pk_name),
    'inet': "'111.111.111.111'"
}

CUSTOM_ANONYMIZATION_RULES = {
    'aggregate_length': lambda column, _: 'length({})'.format(column)
}


DB_ARG_NAMES = ('dbname', 'user', 'password', 'host', 'port')
DB_ENV_NAMES = ('ANONYMIZED_DB_NAME', 'ANONYMIZED_DB_USER', 'ANONYMIZED_DB_PASS', 'ANONYMIZED_DB_HOST',
                'ANONYMIZED_DB_PORT')


class PgantomizerError(Exception):
    pass


class MissingAnonymizationRuleError(PgantomizerError):
    pass


class InvalidAnonymizationSchemaError(PgantomizerError):
    pass


def get_table_pk_name(schema, table):
    return schema[table].get('pk', DEFAULT_PK_COLUMN_NAME) if schema[table] else DEFAULT_PK_COLUMN_NAME


def get_db_args_from_env():
    return {name: os.environ.get(var) for name, var in zip(DB_ARG_NAMES, DB_ENV_NAMES)}


def get_psql_db_args(db_args):
    return '-d {dbname} -U {user} -h {host} -p {port}'.format(**db_args)


def drop_schema(db_args):
    subprocess.run(
        'PGPASSWORD={password} psql {db_args} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" {redirect}'.format(
            password=db_args.get('password'),
            db_args=get_psql_db_args(db_args),
            redirect='' if logging.getLogger().getEffectiveLevel() == logging.DEBUG else '>/dev/null 2>&1'),
        shell=True
    )


def load_db_to_new_instance(filename, db_args):
    if not os.path.isfile(filename):
        raise IOError('Dump file {} is not a file.'.format(filename))
    os.putenv('PGPASSWORD', db_args.get('password'))
    drop_schema(db_args)
    subprocess.run(
        'PGPASSWORD={password} pg_restore -Fc -j 8 {db_args} {filename} {redirect}'.format(
            password=db_args.get('password'),
            db_args=get_psql_db_args(db_args), filename=filename,
            redirect='' if logging.getLogger().getEffectiveLevel() == logging.DEBUG else '>/dev/null 2>&1'),
        shell=True
    )


def prepare_column_for_anonymization(conn, cursor, table, column, data_type):
    """
    Some data types such as VARCHAR are anonymized in such a manner that the anonymized value can be longer that
    the length constrain on the column. Therefore, the constraint is enlarged.
    """
    if data_type == 'character varying':
        logging.debug('Extending length of varchar {}.{}'.format(table, column))
        cursor.execute("ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar(250);".format(
            table=table,
            column=column
        ))
    conn.commit()


def check_schema(cursor, schema, db_args):
    for table in schema:
        try:
            cursor.execute("SELECT {columns} FROM {table};".format(
                columns='"{}"'.format('", "'.join(schema[table].get('raw', []) + [get_table_pk_name(schema, table)])),
                table=table
            ))
        except psycopg2.ProgrammingError as e:
            raise InvalidAnonymizationSchemaError(str(e))


def anonymize_column(cursor, schema, table, column, data_type):
    if column == get_table_pk_name(schema, table) or (schema[table] and column in schema[table].get('raw', [])):
        logging.debug('Skipping anonymization of {}.{}'.format(table, column))
    elif data_type in ANONYMIZE_DATA_TYPE:
        custom_rule = get_in(schema, [table, 'custom_rules', column])
        if custom_rule and custom_rule not in CUSTOM_ANONYMIZATION_RULES:
            raise MissingAnonymizationRuleError('Custom rule "{}" is not defined'.format(custom_rule))
        anonymization = CUSTOM_ANONYMIZATION_RULES[custom_rule] if custom_rule else ANONYMIZE_DATA_TYPE[data_type]
        cursor.execute("UPDATE {table} SET {column} = {value};".format(
            table=table,
            column=column,
            value=anonymization(column, get_table_pk_name(schema, table)) if callable(anonymization) else anonymization
        ))
        logging.debug('Anonymized {}.{}'.format(table, column))
    else:
        raise MissingAnonymizationRuleError('No rule to anonymize type "{}"'.format(data_type))


def anonymize_db(schema, db_args):
    with psycopg2.connect(**db_args) as conn:
        with conn.cursor() as cursor:
            check_schema(cursor, schema, db_args)
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            for table_name in cursor.fetchall():
                cursor.execute("SELECT column_name, data_type FROM information_schema.columns "
                               "WHERE table_schema = 'public' AND table_name = '{}'".format(table_name[0]))
                for column_name, data_type in cursor.fetchall():
                    prepare_column_for_anonymization(conn, cursor, table_name[0], column_name, data_type)
                    anonymize_column(cursor, schema, table_name[0], column_name, data_type)


def load_anonymize_remove(dump_file, schema, leave_dump=False, db_args=None):
    schema = yaml.load(open(schema))
    db_args = db_args or get_db_args_from_env()
    try:
        load_db_to_new_instance(dump_file, db_args)
        anonymize_db(schema, db_args)
    except Exception:  # Any exception must result into droping the schema to prevent sensitive data leakage
        drop_schema(db_args)
        raise
    finally:
        if not leave_dump:
            subprocess.run(['rm', dump_file])


def main():
    parser = argparse.ArgumentParser(description='Load data from a Postgres dump to a specified instance '
                                                 'and anonymize it according to rules specified in a YAML config file.',
                                     epilog='Beware that all tables in the target DB are dropped '
                                            'prior to loading the dump and anonymization. See README.md for details.')
    parser.add_argument('-v', '--verbose', action='count', help='increase output verbosity')
    parser.add_argument('-l', '--leave-dump', action='store_true', help='do not delete dump file after anonymization')
    parser.add_argument('--schema',  help='YAML config file with anonymization rules for all tables', required=True,
                        default='./schema.yaml')
    parser.add_argument('-f', '--dump-file',  help='path to the dump of DB to load and anonymize',
                        default='to_anonymize.sql')
    parser.add_argument('--dbname',  help='name of the database to dump')
    parser.add_argument('--user', help='name of the Postgres user with access to the anonymized database')
    parser.add_argument('--password', help='password of the Postgres user with access to the anonymized database',
                        default='')
    parser.add_argument('--host', help='host where the DB is running', default='localhost')
    parser.add_argument('--port', help='port where the DB is running', default='5432')

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s")

    if not os.path.isfile(args.dump_file):
        sys.exit('File with dump "{}" does not exist.'.format(args.dump_file))

    if not os.path.isfile(args.schema):
        sys.exit('File with schema "{}" does not exist.'.format(args.schema))

    db_args = ({name: value for name, value in zip(DB_ARG_NAMES, (args.dbname, args.user, args.password, args.host,
                                                                  args.port))}
               if args.dbname and args.user else None)

    load_anonymize_remove(args.dump_file, args.schema, args.leave_dump, db_args)


if __name__ == '__main__':
    main()
