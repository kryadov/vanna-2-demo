-- PostgreSQL Demo Schema for Vanna NL2SQL
-- This creates a tiny retail schema with a few rows so you can ask meaningful questions.

-- Drop objects if they already exist (idempotent-ish for local dev)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='order_items') THEN
        DROP TABLE order_items;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='orders') THEN
        DROP TABLE orders;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='products') THEN
        DROP TABLE products;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='customers') THEN
        DROP TABLE customers;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='categories') THEN
        DROP TABLE categories;
    END IF;
END $$;

-- Core tables
CREATE TABLE categories (
    category_id   SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL
);

CREATE TABLE products (
    product_id   SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id  INT REFERENCES categories(category_id),
    unit_price   NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT UNIQUE,
    city        TEXT,
    country     TEXT
);

CREATE TABLE orders (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INT NOT NULL REFERENCES customers(customer_id),
    order_date   DATE NOT NULL,
    status       TEXT NOT NULL DEFAULT 'completed'
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id    INT NOT NULL REFERENCES products(product_id),
    quantity      INT NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0)
);

-- Sample data
INSERT INTO categories (category_name) VALUES
 ('Electronics'),
 ('Books'),
 ('Home & Kitchen');

INSERT INTO products (product_name, category_id, unit_price) VALUES
 ('Wireless Mouse', 1, 25.99),
 ('Mechanical Keyboard', 1, 89.90),
 ('USB-C Hub', 1, 39.50),
 ('Data Science Handbook', 2, 49.00),
 ('Cooking Pan', 3, 29.99);

INSERT INTO customers (first_name, last_name, email, city, country) VALUES
 ('Alice', 'Johnson', 'alice@example.com', 'New York', 'USA'),
 ('Bob',   'Smith',   'bob@example.com',   'London',   'UK'),
 ('Carol', 'Nguyen',  'carol@example.com', 'Sydney',   'Australia');

INSERT INTO orders (customer_id, order_date, status) VALUES
 (1, DATE '2024-01-15', 'completed'),
 (1, DATE '2024-03-22', 'completed'),
 (2, DATE '2024-02-10', 'completed'),
 (3, DATE '2025-06-05', 'completed');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
 (1, 1, 1, 25.99),
 (1, 4, 1, 49.00),
 (2, 2, 1, 89.90),
 (2, 3, 2, 39.50),
 (3, 5, 3, 29.99),
 (4, 2, 1, 89.90),
 (4, 1, 2, 25.99);

-- Helpful view for revenue per order
CREATE OR REPLACE VIEW order_revenue AS
SELECT
  o.order_id,
  o.order_date,
  o.customer_id,
  SUM(oi.quantity * oi.unit_price) AS total_amount
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_date, o.customer_id;

-- Helpful view for revenue per customer per year
CREATE OR REPLACE VIEW customer_revenue_year AS
SELECT
  c.customer_id,
  c.first_name,
  c.last_name,
  EXTRACT(YEAR FROM o.order_date) AS year,
  SUM(oi.quantity * oi.unit_price) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id, c.first_name, c.last_name, EXTRACT(YEAR FROM o.order_date);

-- Indexes for simple performance
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

-- Sanity checks
-- SELECT * FROM order_revenue ORDER BY order_id;
-- SELECT * FROM customer_revenue_year ORDER BY customer_id, year;
