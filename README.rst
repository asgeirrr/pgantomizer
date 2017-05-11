pgantomizer
===========

Anonymize data in your PostgreSQL dababase with ease. Anonymization is handy if you need to provide  data to
people that should not have access to the personal information of the users.
Importing the data to third-party tools where you cannot guarantee what will happen to the data is also a common use case.


Anonymization Process
---------------------

The rules for anonynimization are written in a single YAML file.
Columns that should be left in the raw form without anonymization must be explicitly marked in the schema.
This ensures that adding the new column in the DB without thinking about its sensitivity does not leak the data.
The default name of the primary key is `id` but a custom one can be specified form the table in the schema.

A sample YAML schema can be examined below.

.. code-block:: yaml

    user:
        raw: []
    customer:
        raw: [user_ptr_id, language, currency, citizenship]
        pk: user_ptr_id
    customeraddress:
        raw: [country, customer_id]


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
* add automated tests (TravisCI)
* submit package automatically to PyPI
* add --dry-run argument that will check the schema and output the operations to be performed
