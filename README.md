# seobrain_backend

This backend powers the referral-based web hosting platform with PayPal integration.

## Features
- User registration and authentication
- Referral tracking and logic
- Package management
- Payment tracking (activation and daily payments)
- PayPal REST API integration for one-time and daily payments
- Scheduled job for daily payments after 3 referrals, charging the referrer
- Secure .env for PayPal credentials

## Tech Stack
- Python 3
- Flask
- SQLAlchemy (SQLite or Postgres)
- python-dotenv
- PayPal REST API

## Setup
1. Create a `.env` file with your PayPal credentials and secret keys.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the Flask app: `python app.py`

## Next Steps
- Implement endpoints for registration, referral, and payment logic
- Integrate PayPal API for payment flows
- Add scheduled job for daily payments

---

Replace this README as you build out your backend.