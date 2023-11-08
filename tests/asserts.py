from psycopg2.extras import NamedTupleCursor


def assert_customer_anonymized(customer, name, language, currency, ip):
    assert customer[1] == name
    assert customer[2] == language
    assert customer[3] == currency
    assert str(customer[4]) == ip


def assert_address_anonymized(address, customer_id, address_line, country):
    assert address[1] == customer_id
    assert address[2] == address_line
    assert address[3] == country


def assert_db_empty(db):
    cursor = db.cursor()
    cursor.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public';")
    assert cursor.fetchone()[0] == 0


def assert_db_anonymized(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM customer;")
    customers = cursor.fetchall()
    assert_customer_anonymized(customers[0], "name_1", "fr", "LAT", "111.111.111.111")
    assert_customer_anonymized(customers[1], "name_2", "tlh", "KR", "111.111.111.111")

    cursor.execute("SELECT * FROM customer_address;")
    addresses = cursor.fetchall()
    assert_address_anonymized(addresses[0], 1, "15", "France")
    assert_address_anonymized(addresses[1], 2, "6", "Klingon Empire")
