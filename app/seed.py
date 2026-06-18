from datetime import date

from sqlalchemy.orm import Session

from app.models import Account, Client, Deductible, Liability, Person


def seed_database(db: Session) -> None:
    if db.query(Client).count() > 0:
        return

    married = Client(
        household_name="Miller Family Household",
        marital_status="married",
        monthly_inflow=21500.00,
        monthly_outflow=14250.00,
        private_reserve_balance=98500.00,
        private_reserve_target_override=None,
        property_address="1842 Cedar Ridge Lane, Raleigh, NC",
        property_value=910000.00,
    )
    married.people = [
        Person(role="client1", first_name="Avery", last_name="Miller", dob=date(1977, 5, 14), ssn_last4="4821"),
        Person(role="client2", first_name="Jordan", last_name="Miller", dob=date(1979, 9, 22), ssn_last4="3940"),
    ]
    married.deductibles = [
        Deductible(label="Homeowners insurance", amount=5000.00),
        Deductible(label="Auto insurance", amount=2000.00),
        Deductible(label="Umbrella policy", amount=1000.00),
    ]
    married.accounts = [
        Account(owner="client1", category="retirement", account_type="401K", institution="Schwab", account_last4="1182", balance=684250.40, cash_balance=18250.00),
        Account(owner="client1", category="retirement", account_type="Roth IRA", institution="Fidelity", account_last4="7210", balance=146820.75, cash_balance=4200.00),
        Account(owner="client2", category="retirement", account_type="403B", institution="Vanguard", account_last4="5521", balance=521300.20, cash_balance=12500.00),
        Account(owner="client2", category="retirement", account_type="IRA", institution="Schwab", account_last4="8902", balance=238440.15, cash_balance=6700.00),
        Account(owner="joint", category="non_retirement", account_type="Joint Brokerage", institution="Schwab", account_last4="3319", balance=358900.00, cash_balance=24100.00),
        Account(owner="joint", category="non_retirement", account_type="Savings", institution="Pinnacle Bank", account_last4="7781", balance=84250.00, cash_balance=None),
    ]
    married.liabilities = [
        Liability(liability_type="mortgage", lender="First National Mortgage", interest_rate=3.75, balance=412800.00),
        Liability(liability_type="auto loan", lender="Capital Auto Finance", interest_rate=4.10, balance=21800.00),
    ]

    single = Client(
        household_name="Taylor Greene Household",
        marital_status="single",
        monthly_inflow=12400.00,
        monthly_outflow=7350.00,
        private_reserve_balance=56300.00,
        private_reserve_target_override=52000.00,
        property_address="92 Willow Park Drive, Charlotte, NC",
        property_value=485000.00,
    )
    single.people = [
        Person(role="client1", first_name="Taylor", last_name="Greene", dob=date(1986, 2, 8), ssn_last4="6205"),
    ]
    single.deductibles = [
        Deductible(label="Homeowners insurance", amount=2500.00),
        Deductible(label="Auto insurance", amount=1000.00),
    ]
    single.accounts = [
        Account(owner="client1", category="retirement", account_type="401K", institution="Vanguard", account_last4="6402", balance=318250.00, cash_balance=8800.00),
        Account(owner="client1", category="retirement", account_type="Roth IRA", institution="Schwab", account_last4="1007", balance=94500.00, cash_balance=2100.00),
        Account(owner="client1", category="non_retirement", account_type="Brokerage", institution="Fidelity", account_last4="4509", balance=126400.00, cash_balance=9700.00),
        Account(owner="client1", category="non_retirement", account_type="Checking", institution="Local Credit Union", account_last4="2099", balance=18350.00, cash_balance=None),
    ]
    single.liabilities = [
        Liability(liability_type="mortgage", lender="Regional Home Lending", interest_rate=5.25, balance=286900.00),
    ]

    db.add_all([married, single])
    db.commit()
