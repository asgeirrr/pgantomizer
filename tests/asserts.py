from psycopg2.extras import NamedTupleCursor


def assert_customer_anonymized(customer, name, language, currency, ip):
    assert customer.name == name
    assert customer.language == language
    assert customer.currency == currency
    assert customer.ip == ip


def assert_address_anonymized(address, customer_id, address_line, country):
    assert address.customer_id == customer_id
    assert address.address_line == address_line
    assert address.country == country


def assert_db_empty(db):
    cursor = db.cursor()
    cursor.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public';")
    assert cursor.fetchone()[0] == 0


def assert_db_anonymized(db):
    cursor = db.cursor(cursor_factory=NamedTupleCursor)
    cursor.execute('SELECT * FROM customer;')
    customers = cursor.fetchall()
    assert_customer_anonymized(customers[0], 'name_1', 'fr', 'LAT', '111.111.111.111')
    assert_customer_anonymized(customers[1], 'name_2', 'tlh', 'KR', '111.111.111.111')

    cursor.execute('SELECT * FROM customer_address;')
    addresses = cursor.fetchall()
    assert_address_anonymized(addresses[0], 1, '15', 'France')
    assert_address_anonymized(addresses[1], 2, '6', 'Klingon Empire')
