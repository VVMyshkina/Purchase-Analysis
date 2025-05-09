CREATE TABLE IF NOT EXISTS dim_customers
(
    customer_id UInt64,
    username String,
    email String,
    password_hash String,
    created_at DateTime,
    updated_at DateTime
)
ENGINE = MergeTree
ORDER BY customer_id;

CREATE TABLE IF NOT EXISTS dim_sellers
(
    seller_id UInt64,
    username String,
    email String,
    password_hash String,
    created_at DateTime,
    updated_at DateTime
)
ENGINE = MergeTree
ORDER BY seller_id;

CREATE TABLE IF NOT EXISTS dim_products
(
    product_id UInt64,
    product_name String,
    product_description String,
    category String,
    price Float32,
    seller_id UInt64,
    created_at DateTime,
    updated_at DateTime
)
ENGINE = MergeTree
ORDER BY product_id;

CREATE TABLE IF NOT EXISTS fact_sales
(
    sale_id UInt64,
    customer_id UInt64,
    product_id UInt64,
    seller_id UInt64,
    sale_date DateTime,
    quantity UInt32,
    total_amount Float32
)
ENGINE = MergeTree
ORDER BY sale_id;
