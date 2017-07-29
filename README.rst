pgantomizer
===========

.. image:: https://travis-ci.org/asgeirrr/pgantomizer.svg?branch=master
    :target: https://travis-ci.org/asgeirrr/pgantomizer

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://github.com/asgeirrr/pgantomizer/blob/master/LICENSE

Anonymize data in your PostgreSQL dababase with ease. Anonymization is handy if you need to provide data to
people that should not have access to the personal information of the users.
Importing the data to third-party tools where you cannot guarantee what will happen to the data is also a common use case.


Anonymization Process
---------------------

The rules for anonynimization are written in a single YAML file.
Columns that should be left in the raw form without anonymization must be explicitly marked in the schema.
This ensures that adding the new column in the DB without thinking about its sensitivity does not leak the data.
The default name of the primary key is `id` but a custom one can be specified form the table in the schema.
Primary key is NOT anonymized by default.

A sample YAML schema can be examined below.

.. code:: yaml

    customer:
        raw: [language, currency]
        pk: customer_id
    customer_address:
        raw: [country, customer_id]
        custom_rules:
            address_line: aggregate_length

Sometimes it is needed to use a different anonymization function for a particular column.
It can be specified in the `custom_rules` directive (see example above).
There is a limited set of functions you can choose from. So far

* **aggregate_length** - replaces content of the column with its length (can be used on any type that supports length function)


Calling pgantomizer from the Command Line
-----------------------------------------

`pgantomizer_dump` is a helper script that dumps tables specified in the YAML schema file to a compressed file.

`pgantomizer` is the main script that loads the PostgreSQL dump into a specified instance and then all columns
except primary keys and the ones specified in the schema as `raw` are anonymized according to their data type.
Finally, the dump file is deleted by default to reduce risk of leakage of unanonymized data.


Calling pgantomizer from Python
-------------------------------

You can call the functions to dump anonymize the data from Python.
Please, look at the `dump_db` and `load_anonymize_remove` in the code.
If you are only after anonymizing an existing database, there is a function `anonymize_db`
that will help you do that.
To help integrating the code in complex environments such as a horde of Docker containers,
all database-related arguments can be supplied as environmental variables.


TODO
----
* expand this README
* submit package automatically to PyPI
* add --dry-run argument that will check the schema and output the operations to be performed
