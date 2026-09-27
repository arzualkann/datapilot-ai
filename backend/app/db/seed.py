"""Create varied, non-production e-commerce records for local development."""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker
from psycopg import Cursor, connect

from app.core.config import get_settings


CITIES = [
    "Istanbul",
    "Ankara",
    "Izmir",
    "Bursa",
    "Antalya",
    "Berlin",
    "London",
    "Amsterdam",
]

CATALOG = {
    "Electronics": [
        ("Wireless Headphones", "89.90"),
        ("Portable Charger", "34.50"),
        ("Smart Desk Lamp", "42.00"),
        ("Bluetooth Speaker", "64.90"),
        ("USB-C Hub", "39.00"),
    ],
    "Home & Kitchen": [
        ("Insulated Travel Mug", "24.90"),
        ("Ceramic Serving Bowl", "31.50"),
        ("Cast Iron Skillet", "58.00"),
        ("Bamboo Cutting Board", "22.00"),
        ("Pour Over Coffee Set", "45.00"),
    ],
    "Fitness": [
        ("Yoga Mat", "29.90"),
        ("Resistance Band Set", "19.50"),
        ("Stainless Water Bottle", "27.00"),
        ("Foam Roller", "23.00"),
        ("Training Gloves", "32.00"),
    ],
    "Office": [
        ("Notebook Set", "14.00"),
        ("Ergonomic Mouse Pad", "18.50"),
        ("Mechanical Keyboard", "109.00"),
        ("Monitor Stand", "49.00"),
        ("Cable Organizer", "12.00"),
    ],
    "Accessories": [
        ("Canvas Tote Bag", "16.00"),
        ("Leather Card Holder", "36.00"),
        ("Sunglasses Case", "21.00"),
        ("Travel Organizer", "38.00"),
        ("Minimal Watch Strap", "28.00"),
    ],
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the local DataPilot demo database.")
    parser.add_argument("--customers", type=int, default=250)
    parser.add_argument("--products", type=int, default=75)
    parser.add_argument("--orders", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the four demo tables before inserting new records.",
    )
    return parser.parse_args()


def validate_counts(args: argparse.Namespace) -> None:
    if min(args.customers, args.products, args.orders) < 1:
        raise ValueError("customers, products, and orders must each be at least 1")


def insert_customers(cursor: Cursor, count: int, fake: Faker, rng: random.Random) -> list[int]:
    customer_ids: list[int] = []
    for index in range(count):
        username = f"{fake.user_name()}-{index}"
        cursor.execute(
            """
            INSERT INTO customers (name, email, city)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (fake.name(), f"{username}@example.test", rng.choices(CITIES, weights=[28, 16, 13, 10, 12, 8, 7, 6])[0]),
        )
        customer_ids.append(cursor.fetchone()[0])
    return customer_ids


def insert_products(cursor: Cursor, count: int) -> list[tuple[int, Decimal]]:
    catalog_items = [
        (name, category, Decimal(price))
        for category, products in CATALOG.items()
        for name, price in products
    ]
    product_ids: list[tuple[int, Decimal]] = []
    for index in range(count):
        name, category, price = catalog_items[index % len(catalog_items)]
        suffix = "" if index < len(catalog_items) else f" Edition {index // len(catalog_items) + 1}"
        cursor.execute(
            """
            INSERT INTO products (name, category, price)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (f"{name}{suffix}", category, price),
        )
        product_ids.append((cursor.fetchone()[0], price))
    return product_ids


def insert_orders(
    cursor: Cursor,
    count: int,
    customer_ids: list[int],
    products: list[tuple[int, Decimal]],
    rng: random.Random,
) -> None:
    today = date.today()
    for _ in range(count):
        selected_products = rng.sample(products, k=rng.randint(1, min(5, len(products))))
        line_items: list[tuple[int, int, Decimal]] = []
        for product_id, list_price in selected_products:
            quantity = rng.randint(1, 4)
            discount = Decimal(str(rng.uniform(0.85, 1.00)))
            unit_price = (list_price * discount).quantize(Decimal("0.01"))
            line_items.append((product_id, quantity, unit_price))

        total = sum((unit_price * quantity for _, quantity, unit_price in line_items), Decimal("0.00"))
        cursor.execute(
            """
            INSERT INTO orders (customer_id, order_date, total_amount)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                rng.choice(customer_ids),
                today - timedelta(days=rng.randint(0, 180)),
                total,
            ),
        )
        order_id = cursor.fetchone()[0]
        cursor.executemany(
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
            """,
            [(order_id, product_id, quantity, unit_price) for product_id, quantity, unit_price in line_items],
        )


def main() -> None:
    args = parse_arguments()
    validate_counts(args)
    fake = Faker()
    fake.seed_instance(args.seed)
    rng = random.Random(args.seed)
    settings = get_settings()

    with connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            if args.reset:
                cursor.execute("TRUNCATE order_items, orders, products, customers RESTART IDENTITY CASCADE")

            customer_ids = insert_customers(cursor, args.customers, fake, rng)
            products = insert_products(cursor, args.products)
            insert_orders(cursor, args.orders, customer_ids, products, rng)

    print(f"Seeded {args.customers} customers, {args.products} products, and {args.orders} orders.")


if __name__ == "__main__":
    main()
