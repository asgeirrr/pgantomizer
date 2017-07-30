import os
import subprocess
from types import SimpleNamespace

import pytest
from pytest_postgresql import factories

from pgantomizer.anonymize import (InvalidAnonymizationSchemaError, MissingAnonymizationRuleError,
                                   load_anonymize_remove, load_db_to_new_instance)
from pgantomizer.dump import dump_db
from pgantomizer.dump import main as dump_main
from pgantomizer.anonymize import main as anonymize_main

from .asserts import assert_db_anonymized, assert_db_empty


anonymized_proc = factories.postgresql_proc(port='8765', logsdir='/tmp')
anonymized = factories.postgresql('anonymized_proc')

DUMP_PATH = 'test_dump.sql'
SCHEMA_PATH = 'example_schema.yaml'
ORIGINAL_DB_ARGS = {
    'password': '',
    'dbname': 'tests',
    'user': 'postgres',
    'host': '127.0.0.1',
    'port': '9876'
}
ANONYMIZED_DB_ARGS = {**ORIGINAL_DB_ARGS, **{'port': '8765'}}
DUMP_DB_ARGS = [ORIGINAL_DB_ARGS[arg] for arg in ('dbname', 'user', 'host', 'port')]


@pytest.yield_fixture(scope='function')
def original_db(postgresql):
    """
    Function-scope fixture that loads init data into the Postgres instance that should be dumped.
    """
    cursor = postgresql.cursor()
    cursor.execute(open('tests/init_data.sql', 'r').read())
    postgresql.commit()
    cursor.close()
    yield postgresql


@pytest.yield_fixture(scope='function')
def dumped_db(original_db):
    """
    Function-scope fixture that dumps the original DB and removes the dump file for test repeatability.
    """
    dump_db(DUMP_PATH, SCHEMA_PATH, '', *DUMP_DB_ARGS)
    yield original_db
    if os.path.exists(DUMP_PATH):
        os.remove(DUMP_PATH)


def test_dump_and_load(original_db, anonymized):
    # Dump the database with sensitive info
    dump_db(DUMP_PATH, SCHEMA_PATH, '', *DUMP_DB_ARGS)
    assert os.path.getsize(DUMP_PATH) > 2000

    load_db_to_new_instance(DUMP_PATH, ANONYMIZED_DB_ARGS)

    # Check if only the tables present in the schema YAML spec were dumped and loaded
    cursor = anonymized.cursor()
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    assert set(table[0] for table in cursor.fetchall()) == {'customer', 'customer_address'}

    # Check if customer table has all the records
    cursor.execute('SELECT count(*) FROM customer;')
    assert cursor.fetchone()[0] == 2

    os.remove(DUMP_PATH)


def test_load_anonymize_remove(dumped_db, anonymized):
    assert_db_empty(anonymized)
    load_anonymize_remove(DUMP_PATH, SCHEMA_PATH, leave_dump=False, db_args=ANONYMIZED_DB_ARGS)
    assert_db_anonymized(anonymized)


def test_invalid_custom_rule_raises_exception(dumped_db, anonymized):
    with pytest.raises(MissingAnonymizationRuleError):
        load_anonymize_remove(DUMP_PATH, 'tests/invalid_custom_rule.yaml', leave_dump=False, db_args=ANONYMIZED_DB_ARGS)
    assert_db_empty(anonymized)


def test_missing_anonymization_rule_raises_exception(original_db, anonymized):
    dump_db(DUMP_PATH, 'tests/missing_anonymization_rule.yaml', '', *DUMP_DB_ARGS)
    with pytest.raises(MissingAnonymizationRuleError):
        load_anonymize_remove(DUMP_PATH, 'tests/missing_anonymization_rule.yaml', leave_dump=False,
                              db_args=ANONYMIZED_DB_ARGS)
    assert_db_empty(anonymized)


def test_schema_column_missing_in_db_raises_exception(dumped_db, anonymized):
    with pytest.raises(InvalidAnonymizationSchemaError):
        load_anonymize_remove(DUMP_PATH, 'tests/missing_column.yaml', leave_dump=False, db_args=ANONYMIZED_DB_ARGS)
    assert_db_empty(anonymized)


def test_missing_schema_raises_exception(dumped_db, anonymized):
    with pytest.raises(IOError):
        load_anonymize_remove(DUMP_PATH, 'invalid_path.yaml', leave_dump=False, db_args=ANONYMIZED_DB_ARGS)


def test_command_line_invokation(original_db, anonymized, monkeypatch):
    monkeypatch.setattr('argparse.ArgumentParser.parse_args', lambda self: SimpleNamespace(
        verbose=False,
        schema=SCHEMA_PATH,
        dump_file=DUMP_PATH,
        **{arg: ORIGINAL_DB_ARGS[arg] for arg in ('dbname', 'user', 'host', 'port', 'password')}
    ))
    dump_main()

    assert os.path.getsize(DUMP_PATH) > 2000
    assert_db_empty(anonymized)
    monkeypatch.setattr('argparse.ArgumentParser.parse_args', lambda self: SimpleNamespace(
        verbose=False,
        leave_dump=False,
        schema=SCHEMA_PATH,
        dump_file=DUMP_PATH,
        **{arg: ANONYMIZED_DB_ARGS[arg] for arg in ('dbname', 'user', 'host', 'port', 'password')}
    ))
    anonymize_main()
    assert_db_anonymized(anonymized)
