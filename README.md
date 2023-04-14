(Start of only human written block)

  This was a project to see how GPT-4 could build something complex. Humans wrote 0 lines of code. 
  
(End of only human written block)

# GearUp Engineers Store

This Flask web application serves as an online store for engineering products. The key features and components of this application include:

1. **Frontend Interface**: Displays a list of available products.
2. **Search Functionality**: Allows users to search for specific products.
3. **ShipStation API Integration**: Fetches product information from ShipStation.
4. **Chatbot Feature**: Utilizes OpenAI's GPT-4 model to assist users with questions about the store and ShipStation app.
5. **Caching Mechanism**: Implements `flask_caching` to cache the results of API calls for a specified duration.
6. **SQLite Database**: Stores chat messages.
7. **Dockerfile**: Containerizes the application.
8. **Flask Routing and Template Inheritance**: Includes a blog page and store page.
9. **README.md**: Provides information on the project, setup, and environment variables.
10. **Unique and Creative Products**: Tailored for engineers, including alcoholic beverages.

The application provides a user-friendly interface for engineers to browse and purchase products while also offering assistance through the integrated chatbot feature.


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

Create a .env file in the root directory and add your ShipStation API key:

```makefile
SHIPSTATION_API_KEY=your_shipstation_api_key
SHIPSTATION_API_SECRET=your_shipstation_api_secret
```

The application should now be running on http://localhost:5000.

Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

License
MIT
