# Custom Store

Custom Store is a simple online store built with Flask, Bootstrap, and Stripe Checkout. It integrates with ShipStation to manage orders and inventory. The web app showcases various products, allows users to search and filter products, and securely processes payments using Stripe.

## Features

- Fetches product inventory from ShipStation API
- Product search with real-time filtering
- Stripe Checkout integration for secure payments
- Success modal with random funny thank you messages and emojis
- ShipStation API integration for order placement

## Getting Started

### Prerequisites

- Python 3.7+
- Flask
- Stripe account with API key

## Setting Up Environment Variables

To run this application, you will need to set up the following environment variables:

1. `OPENAI_API_KEY`: Your OpenAI API key, which can be obtained from the OpenAI platform.
2. `SHIPSTATION_API_KEY`: Your ShipStation API key, found in your ShipStation account settings.
3. `SHIPSTATION_API_SECRET`: Your ShipStation API secret, also found in your ShipStation account settings.

You can set these environment variables using a `.env` file or by exporting them directly in your terminal. Here's an example of how to create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
SHIPSTATION_API_KEY=your_shipstation_api_key
SHIPSTATION_API_SECRET=your_shipstation_api_secret
```

### Installation

Create a virtual environment, activate it, install the required packages, and run the Flask app:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

Create a .env file in the root directory and add your Stripe API key and ShipStation API key:

```makefile
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
SHIPSTATION_API_KEY=your_shipstation_api_key
SHIPSTATION_API_SECRET=your_shipstation_api_secret
```

The application should now be running on http://localhost:5000.

Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

License
MIT