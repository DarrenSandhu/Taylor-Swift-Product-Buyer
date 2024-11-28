"""
Taylor Swift Store Bot
========================

This Python script automates product monitoring and checkout for the Taylor Swift UK store. It tracks the availability of specified products, notifies you via email when they're in stock, and attempts to complete the checkout process.

Features:
---------
1. Product Monitoring: Continuously monitors a list of product URLs for stock availability.
2. Email Notifications: Sends an email when a product becomes available.
3. Automated Checkout: Adds products to the cart and attempts to complete the checkout process using saved payment and shipping information.
4. Error Handling: Logs errors and retries failed operations, ensuring robustness.

Requirements:
-------------
- Python 3.9+
- Required Python libraries:
  - os
  - time
  - requests
  - BeautifulSoup (bs4)
  - smtplib
  - logging
  - selenium
  - python-dotenv

Ensure these dependencies are installed. Use the `requirements.txt` file to install them:
```bash
pip install -r requirements.txt
```

Setup:
--------------

1. Install Dependencies: Run the following to install required packages:
```bash
pip install -r requirements.txt
```

2. Set Up Environment Variables: Create a .env file in the root directory to store sensitive information like payment and shipping details. Ensure the following variables are defined in the .env file:
```bash
CARD_NAME=Your Name
CARD_NUMBER=Your Card Number
CARD_EXPIRY_MONTH=MM
CARD_EXPIRY_YEAR=YY
CARD_CVV=Your CVV

SHIPPING_FIRST_NAME=Your First Name
SHIPPING_LAST_NAME=Your Last Name
SHIPPING_ADDRESS=Your Address
SHIPPING_CITY=Your City
SHIPPING_POSTCODE=Your Postal Code
SHIPPING_COUNTRY=Your Country
SHIPPING_EMAIL=Your Email
SHIPPING_PHONE=Your Phone Number

EMAIL=Your Email Notifier
PASSWORD=Your App Password
TO_EMAILS=Emails To Notify
SMTP_SERVER=Your SMTP Server
SMTP_PORT=Your SMTP Port
```

3. Install WebDriver: Download and install the appropriate version of ChromeDriver for your browser version from here. Ensure the ChromeDriver executable is in your system's PATH or specify its location in the script.

4. Update Product URLs: Edit the PRODUCT_URLS list in the script to include the products you want to monitor:

Usage:
--------------
1. Run the Script: Execute the script with:
```bash
python3 productChecker.py
```

2. Monitor Logs: The script logs activity to the console, including stock status, errors, and checkout progress.

3. Email Notifications: When a product is in stock, you’ll receive an email with details.

Troubleshooting:
---------------

1. Dependencies Not Found: Ensure all required libraries are installed using pip install -r requirements.txt.

2. Environment Variables Not Loaded: Verify the .env file exists in the correct directory and contains all required variables.

3. WebDriver Issues: Ensure the ChromeDriver version matches your Chrome browser version.

4. Failed Email Notifications: Double-check email credentials and app-specific passwords if using Gmail.

Disclaimer:
---------------

This bot is for educational purposes only. Automating purchases may violate the terms and conditions of the store. Use responsibly.
