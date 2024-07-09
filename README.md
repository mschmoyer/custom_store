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

```makefile
export SHIPSTATION_API_KEY=your_shipstation_api_key
export SHIPSTATION_API_SECRET=your_shipstation_api_secret
export OPENAI_API_KEY=your_openai_key
```

## Running the Server

```bash
pip3 install -r requirements.txt
python3 setup_db.py #one time.
python3 app.py
```

The application should now be running on http://localhost:5000.

Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

License
MIT
