# PayChangu-Payment-API

A Python wrapper for the PayChangu payment gateway API. Process payments and payouts in Malawi with minimal code.

## Features

- 💳 Payment processing with checkout URLs
- 💰 Bank transfers and mobile money payouts  
- 📱 Auto-detection for Airtel Money and TNM Mpamba
- ✅ Payment and payout verification
- 🛡️ Simple error handling

## Installation

```bash
pip install requests
```

Download `paychangu.py` and import:

```python
from paychangu import PayChanguAPI

api = PayChanguAPI("your_api_key")
```

## Quick Example

```python
# Create payment
payment = api.create_payment(
    amount=1000.0,
    email="user@email.com", 
    first_name="John",
    last_name="Doe",
    callback_url="https://yoursite.com/webhook",
    return_url="https://yoursite.com/success"
)

# Get checkout URL
if payment["success"]:
    print(payment["checkout_url"])

# Create mobile payout
payout = api.create_mobile_payout(500.0, "0881234567")
```

## Requirements

- Python 3.6+
- PayChangu API key

## License

MIT
