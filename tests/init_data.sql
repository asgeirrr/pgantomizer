CREATE TABLE customer (
    customer_id serial PRIMARY KEY,
    name varchar NOT NULL,
    language varchar NOT NULL,
    currency varchar NOT NULL,
    ip inet NOT NULL
);

CREATE TABLE customer_address (
    id serial PRIMARY KEY,
    customer_id serial references customer(customer_id),
    address_line varchar NOT NULL,
    country varchar NOT NULL
);

CREATE TABLE  delivery (
    id serial PRIMARY KEY,
    customer_id serial references customer(customer_id),
    item_name varchar NOT NULL,
    item_address cidr NOT NULL
);

INSERT INTO customer VALUES (1, 'Jean-Luc Picard', 'fr', 'LAT', '192.222.222.222');
INSERT INTO customer VALUES (2, 'Worf, son of Mogh', 'tlh', 'KR', '192.111.111.111');
INSERT INTO customer_address VALUES (1, 1, 'Le Puy-en-Velay', 'France');
INSERT INTO customer_address VALUES (2, 2, 'Kronos', 'Klingon Empire');
INSERT INTO delivery VALUES (1, 1, 'Phaser Mark VI', '123.123.123.123');
