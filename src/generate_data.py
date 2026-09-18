import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

random.seed(42)


def random_case_and_space(email: str) -> str:
    """Injects casing noise and whitespace into strings."""
    mutations = [
        email.lower(),
        email.upper(),
        email.capitalize(),
        f"  {email} ",
        f"{email}  ",
    ]
    return random.choice(mutations)


def generate_raw_data(num_accounts: int = 150, num_events: int = 1200) -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    base_start = datetime(2025, 1, 1, tzinfo=UTC)
    tier_prices = {"Starter": 99.0, "Growth": 499.0, "Enterprise": 2499.0}

    sf_rows = []
    account_lookup = {}  # email -> account_id

    for i in range(1, num_accounts + 1):
        account_id = f"SF_{i:04d}"
        company_name = f"Company_{i}"
        clean_email = f"billing@company{i}.com"
        account_lookup[clean_email] = account_id

        current_time = base_start + timedelta(days=random.randint(0, 180))
        current_tier = random.choice(["Starter", "Growth"])

        sf_rows.append(
            {
                "Account_Id": account_id,
                "Company_Name": (
                    f" {company_name} " if random.random() < 0.3 else company_name
                ),
                "Contact_Email": random_case_and_space(clean_email),
                "Tier": current_tier,
                "Updated_At": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # 40% chance the company upgrades or changes tiers later (tests SCD Type 2)
        if random.random() < 0.4:
            upgrade_time = current_time + timedelta(days=random.randint(60, 200))
            new_tier = "Enterprise" if current_tier == "Growth" else "Growth"
            sf_rows.append(
                {
                    "Account_Id": account_id,
                    "Company_Name": company_name,
                    "Contact_Email": random_case_and_space(clean_email),
                    "Tier": new_tier,
                    "Updated_At": upgrade_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    stripe_rows = []
    all_emails = list(account_lookup.keys())

    for sub_idx in range(1, num_events + 1):
        # 95% of events map to an account; 5% are orphan/ghost payments to challenge the pipeline
        if random.random() < 0.95:
            chosen_email = random.choice(all_emails)
        else:
            chosen_email = f"ghost_user_{sub_idx}@unknowncorp.io"

        event_time = base_start + timedelta(
            days=random.randint(0, 500),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        status = random.choices(
            ["active", "past_due", "canceled"], weights=[0.8, 0.1, 0.1]
        )[0]
        base_plan = random.choice(list(tier_prices.values()))

        stripe_rows.append(
            {
                "sub_id": f"sub_{sub_idx:06d}",
                "customer_email": random_case_and_space(chosen_email),
                "plan_amount_usd": float(base_plan),
                "status": status,
                "event_timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    df_sf = pl.DataFrame(sf_rows)
    df_stripe = pl.DataFrame(stripe_rows)

    df_sf.write_csv(data_dir / "raw_salesforce_accounts.csv")
    df_stripe.write_csv(data_dir / "raw_stripe_subscriptions.csv")

    print(
        f"Generated {len(df_sf)} Salesforce records across {num_accounts} accounts.\n"
        f"Generated {len(df_stripe)} Stripe billing events (including ghost records)."
    )


if __name__ == "__main__":
    generate_raw_data()
