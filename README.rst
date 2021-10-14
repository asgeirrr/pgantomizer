pgantomizer
===========

.. image:: https://travis-ci.org/asgeirrr/pgantomizer.svg?branch=master
    :target: https://travis-ci.org/asgeirrr/pgantomizer

.. image:: https://coveralls.io/repos/github/asgeirrr/pgantomizer/badge.svg?branch=master
    :target: https://coveralls.io/github/asgeirrr/pgantomizer

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://github.com/asgeirrr/pgantomizer/blob/master/LICENSE

.. image:: https://badge.fury.io/py/pgantomizer.svg
    :target: https://badge.fury.io/py/pgantomizer

Anonymize data in your PostgreSQL dababase with ease. Anonymization is handy if you need to provide data to
people that should not have access to the personal information of the users.
Importing the data to third-party tools where you cannot guarantee what will happen to the data is also a common use case.
This tool will come in handy when GDPR will take effect in EU-countries.


Anonymization Process
---------------------

The rules for anonynimization are written in a single YAML file.

Columns that should be left in the raw form without anonymization must be explicitly marked in the schema.
This ensures that adding the new column in the DB without thinking about its sensitivity does not leak the data.

The default name of the primary key is `id` but a custom one can be specified form the table in the schema.
If the table has no primary key, you may specify `~` or `null` explicitly. Primary key is NOT anonymized by default.

If you wish do bypass anonymization and truncate a specific table, you can do so by passing `truncate: true`.

You can limit the scope of the anonymization pass by providing a `where` clause. This is useful for retaining
internal data as appropriate.


A sample YAML schema can be examined below.

.. code:: yaml

    customer:
        raw: [language, currency]
        pk: customer_id
        custom_rules:
            email: example_email,
            bio: x_out,
            auth_hash: clear,
            another_uniq_id: md5,
            phone_number:
                value: '+15555555555'
        where: "email <> 'me@my-company.com'"

    customer_address:
        raw: [country, customer_id]
        pk: ~
        custom_rules:
            address_line: aggregate_length

    customer_transactions:
        truncate: true

Sometimes it is needed to use a different anonymization function for a particular column.
It can be specified in the `custom_rules` directive (see example above).
There is a limited set of functions you can choose from. So far:

* **aggregate_length** - replaces content of the column with its length (can be used on any type that supports length function)
* **clear** - simply nulls out the value (whatever DB constraints still apply)
* **example_email** - replaces the value with an `@example.com` based on the primary key value
* **md5** - alternative to default TEXT handling, useful for creating variance aside default handling while also guaranteeing value uniqueness
* **x_out** - converts a string alpha-numeric characters to X's, retaining length

Additionally, you can provide a nested value with a `value` key to assign values directly.


Calling pgantomizer from the Command Line
-----------------------------------------

**pgantomizer_dump** is a helper script that dumps tables specified in the YAML schema file to a compressed file using `pg_dump`.
Just pass the path to the schema and the DB connection details.
Minimal working example taking advantage of default values of some of the required parameters:

.. code:: bash

    pgantomizer_dump --schema my_schema.yaml --dbname original_postgres --user alaric

To see a list of all parameters, run:

.. code:: bash

    pgantomizer_dump -h

The script is able to take the DB connection details from environmental variables
following the conventions of running Django in Docker. The presumed variable names are:
`DB_DEFAULT_NAME`, `DB_DEFAULT_USER`, `DB_DEFAULT_PASS`, `DB_DEFAULT_SERVICE`, `DB_DEFAULT_PORT`.

By default, the main script, **pgantomizer** loads the Postgre dump into a specified instance. Then all columns
except primary keys and the ones specified in the schema as `raw` are anonymized according to their data type.
Finally, the dump file is deleted by default to reduce risk of leakage of unanonymized data.
The connection details of the Postgres instance where the anonymized data should be loaded can be passed as arguments


.. code:: bash

    pgantomizer --schema my_schema.yaml --dump-file ./to_anonymize.sql --dbname anonymized_postgres --user alaric --password anonymized_pass --host localhost --port 5432

or through environmental variables with following names:
`ANONYMIZED_DB_NAME`, `ANONYMIZED_DB_USER`, `ANONYMIZED_DB_PASS`, `ANONYMIZED_DB_HOST`, `ANONYMIZED_DB_PORT`.

Note: If you wish to anonymize a source that has been previously restored using other means, you may do so by passing the `--skip-restore` (`-s`) flag to pgantomizer.
In this mode pgantomizer will not try to enforce any dump file requirements and will connect directly to the target server for anonymization without any schema reconstruction.


Calling pgantomizer from Python
-------------------------------

Use **dump_db** and **load_anonymize_remove** functions to dump anonymize the data from Python.
In the following example, DB connections for the original and anonymized instance are specified via ENV variables described above.

.. code:: python

    from pgantomizer import dump_db, load_anonymize_remove

    dump_db('to_anonymize.sql', 'anonymization_schema.yaml')
    load_anonymize_remove('to_anonymize.sql', 'anonymization_schema.yaml')

Both functions have an optional **db_args** argument to pass the connection arguments explicitly in a dict.
See the example below how the dict should look like.

If you are only after anonymizing an existing database, there is a function `anonymize_db`
that will help you do that with a little extra work of parsing the YAML schema.

.. code:: python

    import yaml

    from pgantomizer import anonymize_db

    anonymize_db(yaml.load(open('anonymization_schema.yaml'), Loader=yaml.FullLoader), {
        'dbname': 'anonymized_postgres',
        'user': 'alaric',
        'password': 'anonymized_pass',
        'host': 'localhost',
        'port': '5432',
    })

If you would like to use environmental variables instead, use function `anonymize.get_db_args_from_env`
to construct the dict from ENV.


TODO
----
* expand this README
* submit package automatically to PyPI
* add --dry-run argument that will check the schema and output the operations to be performed
* remove password argument and use `getpass` instead for better security
