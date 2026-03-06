"""
Alpaca Account Provisioning - Auto-creates sandbox brokerage accounts for new users.
"""

import os
import random
import logging
from datetime import datetime, timezone

from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import (
    CreateAccountRequest,
    Contact,
    Identity,
    Disclosures,
    Agreement,
    CreateACHRelationshipRequest,
)
from alpaca.broker.enums import AgreementType, BankAccountType

logger = logging.getLogger(__name__)


def _get_broker() -> BrokerClient:
    return BrokerClient(
        api_key=os.getenv("APCA_BROKER_KEY_ID"),
        secret_key=os.getenv("APCA_BROKER_SECRET_KEY"),
        sandbox=True,
    )


def _random_ssn() -> str:
    """Generate a random fake SSN for sandbox account creation."""
    area = random.randint(100, 899)
    group = random.randint(10, 99)
    serial = random.randint(1000, 9999)
    return f"{area}-{group}-{serial}"


def create_alpaca_account_for_user(username: str) -> dict:
    """
    Creates a new Alpaca sandbox brokerage account + ACH relationship.

    Returns:
        dict with "account_id" and "relationship_id" on success,
        or dict with "error" on failure.
    """
    client = _get_broker()
    now = datetime.now(timezone.utc).isoformat()

    try:
        account = client.create_account(
            CreateAccountRequest(
                contact=Contact(
                    email_address=f"{username}@sandbox.trading-app.local",
                    phone_number="+12125550100",
                    street_address=["123 Trading Street"],
                    city="New York",
                    state="NY",
                    postal_code="10001",
                ),
                identity=Identity(
                    given_name=username.capitalize(),
                    family_name="Trader",
                    date_of_birth="1990-01-15",
                    tax_id=_random_ssn(),
                    tax_id_type="USA_SSN",
                    country_of_tax_residence="USA",
                    funding_source=["employment_income"],
                ),
                disclosures=Disclosures(
                    is_control_person=False,
                    is_affiliated_exchange_or_finra=False,
                    is_politically_exposed=False,
                    immediate_family_exposed=False,
                ),
                agreements=[
                    Agreement(
                        agreement=AgreementType.CUSTOMER,
                        signed_at=now,
                        ip_address="127.0.0.1",
                    ),
                    Agreement(
                        agreement=AgreementType.ACCOUNT,
                        signed_at=now,
                        ip_address="127.0.0.1",
                    ),
                ],
            )
        )
        logger.info("Created Alpaca account %s for user '%s'", account.id, username)
    except Exception as e:
        logger.error("Failed to create Alpaca account for '%s': %s", username, e)
        return {"error": f"Alpaca account creation failed: {e}"}

    # Create ACH relationship so the user can deposit funds
    relationship_id = None
    try:
        ach = client.create_ach_relationship_for_account(
            account_id=account.id,
            ach_data=CreateACHRelationshipRequest(
                account_owner_name=f"{username.capitalize()} Trader",
                bank_account_type=BankAccountType.CHECKING,
                bank_account_number="32165498720",
                bank_routing_number="121000358",
            ),
        )
        relationship_id = str(ach.id)
        logger.info("Created ACH relationship %s for account %s", relationship_id, account.id)
    except Exception as e:
        logger.warning("ACH relationship creation failed (non-fatal): %s", e)

    return {
        "account_id": str(account.id),
        "relationship_id": relationship_id,
    }
