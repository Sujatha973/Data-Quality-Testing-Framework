"""
Generates realistic sample data for two tables: customers and orders.

Pure standard-library implementation (no third-party deps needed just to
generate data) so it runs anywhere with plain `python3`.

Intentionally seeds a handful of data quality issues (nulls, duplicates,
invalid emails, orphan foreign keys, negative amounts) so the DQ framework
has real failures to detect and report on -- not just green checkmarks.

Usage:
    python3 generate_sample_data.py
Outputs:
    customers.csv
    orders.csv
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

NUM_CUSTOMERS = 200
NUM_ORDERS = 800

STATUSES = ["placed", "shipped", "delivered", "cancelled", "returned"]
COUNTRIES = ["USA", "India", "UK", "Germany", "Canada", "Australia"]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Priya",
    "Arjun", "Ananya", "Rohan", "Kavya", "Wei", "Hiro", "Emma", "Liam",
    "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mateo", "Lucia",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Sharma", "Patel", "Nair", "Khan", "Chen", "Tanaka", "Muller", "Rossi",
]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_email(name):
    user = name.lower().replace(" ", ".")
    domain = random.choice(["gmail.com", "outlook.com", "yahoo.com", "company.co", "mail.com"])
    return f"{user}{random.randint(1,999)}@{domain}"


def random_date(start_days_ago, end_days_ago):
    delta_days = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=delta_days)).date()


def generate_customers(n):
    rows = []
    for i in range(1, n + 1):
        customer_id = i
        full_name = random_name()
        email = random_email(full_name)

        # Seed ~3% invalid emails (missing @ replaced)
        if random.random() < 0.03:
            email = email.replace("@", "_at_")

        # Seed a handful of duplicate emails (~2%)
        if i > 5 and random.random() < 0.02:
            email = rows[random.randint(0, len(rows) - 1)]["email"]

        # Seed a few null names (~2%)
        if random.random() < 0.02:
            full_name = ""

        signup_date = random_date(1095, 1)

        rows.append(
            {
                "customer_id": customer_id,
                "full_name": full_name,
                "email": email,
                "country": random.choice(COUNTRIES),
                "signup_date": signup_date.isoformat(),
            }
        )

    # Seed a couple of duplicate customer_ids to break uniqueness on purpose
    if n >= 10:
        dup = dict(rows[3])
        dup["customer_id"] = rows[7]["customer_id"]
        rows.append(dup)

    return rows


def generate_orders(n, max_customer_id):
    rows = []
    for i in range(1, n + 1):
        order_id = i
        customer_id = random.randint(1, max_customer_id)

        # Seed ~2% orphan foreign keys (customer_id that doesn't exist)
        if random.random() < 0.02:
            customer_id = max_customer_id + random.randint(100, 999)

        order_date = random_date(365, 0)
        amount = round(random.uniform(5, 500), 2)

        # Seed ~1.5% negative amounts (data entry errors / refund mis-signs)
        if random.random() < 0.015:
            amount = -amount

        status = random.choice(STATUSES)

        # Seed ~1% null status
        if random.random() < 0.01:
            status = ""

        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date.isoformat(),
                "amount": amount,
                "status": status,
            }
        )

    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {path}")


if __name__ == "__main__":
    customers = generate_customers(NUM_CUSTOMERS)
    orders = generate_orders(NUM_ORDERS, NUM_CUSTOMERS)

    write_csv(
        "customers.csv",
        customers,
        ["customer_id", "full_name", "email", "country", "signup_date"],
    )
    write_csv(
        "orders.csv",
        orders,
        ["order_id", "customer_id", "order_date", "amount", "status"],
    )
