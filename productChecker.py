import os
import time
import requests
from bs4 import BeautifulSoup
import smtplib
import logging
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
load_dotenv()



# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
card_name = os.getenv("CARD_NAME")
card_number = os.getenv("CARD_NUMBER")
card_expiry_month = os.getenv("CARD_EXPIRY_MONTH")
card_expiry_year = os.getenv("CARD_EXPIRY_YEAR")
card_cvv = os.getenv("CARD_CVV")

shipping_first_name = os.getenv("SHIPPING_FIRST_NAME")
shipping_last_name = os.getenv("SHIPPING_LAST_NAME")
shipping_address = os.getenv("SHIPPING_ADDRESS")
shipping_city = os.getenv("SHIPPING_CITY")
shipping_postal_code = os.getenv("SHIPPING_POSTCODE")
shipping_country = os.getenv("SHIPPING_COUNTRY")
shipping_email = os.getenv("SHIPPING_EMAIL")
shipping_phone = os.getenv("SHIPPING_PHONE")

print(shipping_address)

# Base checkout URL
BASE_CHECKOUT_URL = "https://storeuk.taylorswift.com/checkouts/cn/"

# Product URLs
PRODUCT_URLS = [
    "https://storeuk.taylorswift.com/products/ttpd-typewriter-ornament", 
    "https://storeuk.taylorswift.com/products/red-taylors-version-guitar-ornament",
    "https://storeuk.taylorswift.com/products/acoustic-piano-ornament",
    "https://storeuk.taylorswift.com/products/folklore-album-hourglass-ornament",
    "https://storeuk.taylorswift.com/products/taylor-swift-midnights-vigilante-chair-ornament",
    "https://storeuk.taylorswift.com/products/folklore-album-cardigan-socks"
    ]

# Email configuration
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TO_EMAILS = os.getenv("TO_EMAILS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")

# Shipping information
shipping_info = {
        'country': shipping_country,
        'email': shipping_email,
        'first_name': shipping_first_name,
        'last_name': shipping_last_name,
        'address1': shipping_address,
        'address2': '',
        'city': shipping_city,
        'postal_code': shipping_postal_code,
        'phone': shipping_phone
    }

# Payment information
payment_info = {
    'number': card_number,
    'expiry_month': card_expiry_year,
    'expiry_year': card_expiry_month,
    'cvv': card_cvv
}

payment_info_no_env = {
    'number': '5356 7401 1391 2604',
    'expiry_month': '03',
    'expiry_year': '27',
    'cvv': '941'
}

INSTOCK_URLS = [
    "https://storeuk.taylorswift.com/products/i-love-you-its-ruining-my-life-boxy-cropped-crewneck-1",
    "https://storeuk.taylorswift.com/products/the-tortured-poets-department-candle",
    "https://storeuk.taylorswift.com/products/1989-taylors-version-seagull-design-tee"
]

# Set of product names that have already been notified
notified_products = set()

# Set up web driver
def configure_chrome_options():
    """Configure Chrome options for headless browsing."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    logging.info("Chrome options configured")
    return chrome_options

driver = webdriver.Chrome(options=configure_chrome_options())
driver.set_page_load_timeout(20)

#####################################################
#####################################################
#####################################################


def fetch_url(url, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.ChunkedEncodingError as e:
            logging.warning(f"ChunkedEncodingError: {e}. Retrying {attempt + 1}/{retries}...")
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None
    return None

def check_product_and_get_name(url):
    response = fetch_url(url)
    if not response:
        return None, None
    soup = BeautifulSoup(response.content, 'html.parser')
    product_name = soup.find("h1", class_="product__title").get_text(strip=True)
    add_to_cart_button = soup.find("button", class_="product-form__submit button button--primary")
    if add_to_cart_button:
        button_text = add_to_cart_button.get_text(strip=True).lower()
        in_stock = "add to cart" in button_text
        return in_stock, product_name
    return False, product_name

def send_notification(url, product_name):
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            subject = f"{product_name} is now in stock!"
            body = f"The {product_name} is now in stock: {url}"
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(EMAIL, TO_EMAILS, message)
        logging.info(f"Email sent for {product_name}.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def get_variant_id(soup):
    """Extract the variant ID from the product page"""
    try:
        # Look for the variant ID in the JSON data
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if 'variants' in str(data):
                    if isinstance(data, dict) and 'variants' in data:
                        return str(data['variants'][0]['id'])
            except json.JSONDecodeError:
                continue
        
        # Fallback: Look for variant ID in form input
        variant_input = soup.find('input', {'name': 'id'})
        if variant_input and 'value' in variant_input.attrs:
            return variant_input['value']
        
    except Exception as e:
        logging.error(f"Error getting variant ID: {e}")
    
    return None


def add_to_cart(url):
    """Add product to cart using requests"""
    try:
        session = requests.Session()
        
        # Set up headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://storeuk.taylorswift.com',
            'Referer': url
        }
        
        # Get the product page
        response = fetch_url(url)
        if not response:
            logging.error("Failed to fetch product page")
            return False
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if product is in stock
        add_to_cart_button = soup.find("button", class_="product-form__submit button button--primary")
        if not add_to_cart_button:
            logging.error("Add to cart button not found")
            return False
            
        button_text = add_to_cart_button.get_text(strip=True).lower()
        if "add to cart" not in button_text:
            logging.info("Product is out of stock")
            return False
            
        # Get variant ID
        variant_id = get_variant_id(soup)
        if not variant_id:
            logging.error("Could not find variant ID")
            return False
            
        logging.info(f"Found variant ID: {variant_id}")
        
        # Prepare cart add request
        cart_url = "https://storeuk.taylorswift.com/cart/add.js"
        payload = {
            "items": [{
                "id": variant_id,
                "quantity": 1
            }]
        }
        
        # Add to cart
        cart_response = session.post(
            cart_url,
            json=payload,
            headers=headers
        )
        
        if cart_response.status_code == 200:
            logging.info("Successfully added to cart")
            # response_data = cart_response.json()
            # logging.info(f"Cart response: {response_data}")
            cart_cookie = cart_response.cookies.get('cart').split('%')[0]
            if cart_cookie:
                logging.info(f"Cart cookie: {cart_cookie}")
            else:
                logging.error("Cart cookie not found")
            checkout_url = f"https://storeuk.taylorswift.com/checkouts/cn/{cart_cookie}"
            return checkout_url
        else:
            logging.error(f"Failed to add to cart. Status: {cart_response.status_code}")
            logging.error(f"Response: {cart_response.text}")
            return False
            
    except Exception as e:
        driver.save_screenshot("add_to_cart_error.png")
        logging.error(f"Error in add_to_cart: {e}")
        return False





def fill_shipping_info(driver, shipping_info):
    """Fill in the shipping information."""
    try:
        logging.info("Filling shipping information")
        wait = WebDriverWait(driver, 120)
        wait.until(EC.presence_of_element_located((By.ID, "email")))
        driver.find_element(By.ID, "emai").send_keys(shipping_info['email'])

        wait.until(EC.presence_of_element_located((By.ID, "Select0")))
        driver.find_element(By.ID, "Select0").send_keys(shipping_info['country'])

        wait.until(EC.presence_of_element_located((By.ID, "TextField0")))
        driver.find_element(By.ID, "TextField0").send_keys(shipping_info['first_name'])

        wait.until(EC.presence_of_element_located((By.ID, "TextField1")))
        driver.find_element(By.ID, "TextField1").send_keys(shipping_info['last_name'])

        wait.until(EC.presence_of_element_located((By.ID, "shipping-address1")))
        driver.find_element(By.ID, "shipping-address1").send_keys(shipping_info['address1'])

        wait.until(EC.visibility_of_element_located((By.ID, "shipping-address1-options")))
        time.sleep(0.5)

        driver.find_element(By.ID, "shipping-address1-option-0").click()  # Select the first address
        driver.find_element(By.ID, "TextField5").send_keys(shipping_info['phone'])
        logging.info("Shipping information filled successfully.")
    except Exception as e:
        driver.save_screenshot("shipping_error.png")
        logging.error(f"Error filling shipping information: {e}")


def fill_payment_info(driver, payment_info):
    """Fill in the payment information."""
    try:
        logging.info("Filling payment information")

        # Fill in the card number
        card_number_iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='card-fields-number-']"))
        )
        driver.switch_to.frame(card_number_iframe)
        driver.find_element(By.ID, "number").send_keys(payment_info['number'])

        # Fill in the expiry date
        driver.switch_to.default_content()
        card_expiry_iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='card-fields-expiry-']"))
        )
        driver.switch_to.frame(card_expiry_iframe)
        driver.find_element(By.ID, "expiry").send_keys(payment_info['expiry_month'])
        time.sleep(1)
        driver.find_element(By.ID, "expiry").send_keys(payment_info['expiry_year'])

        # Fill in the CVV
        driver.switch_to.default_content()
        card_cvv_iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='card-fields-verification_value-']"))
        )
        driver.switch_to.frame(card_cvv_iframe)
        driver.find_element(By.ID, "verification_value").send_keys(payment_info['cvv'])

        driver.switch_to.default_content()
        logging.info("Payment information filled successfully.")
    except Exception as e:
        driver.save_screenshot("payment_error.png")
        logging.error(f"Error filling payment information: {e}")

def checkout(checkout_url, shipping_info, payment_info):
    """Automate the checkout process with improved session handling"""
    try:
        # Now attempt to access the checkout URL
        success = False
        attempt = 0
        while not success:
            attempt += 1
            try:
                driver.get(checkout_url)
                # Check if we're still on the checkout page
                if "checkout" in driver.current_url:
                    logging.info("Successfully reached checkout page")
                    
                    #####################################################
                    #   Fill in the shipping information here            #
                    #####################################################

                    fill_shipping_info(driver, shipping_info)

                    #####################################################
                    #####################################################

                    
            
                    #####################################################
                    #   Fill in the payment information here            #
                    #####################################################

                    fill_payment_info(driver, payment_info)

                    #####################################################
                    #####################################################

                    driver.switch_to.default_content()
                    # Click Pay Now button
                    pay_now_button = driver.find_element(By.ID, "checkout-pay-button")
                    if pay_now_button:
                        pay_now_button.click()
                        logging.info("Clicked Pay Now button")
                        time.sleep(100)
                        success = True  
                    else:
                        logging.error("Pay Now button not found")
                
                else:
                    logging.warning(f"Attempt {attempt}: Not on checkout page, current URL: {driver.current_url}")
                    time.sleep(20)
                    
            except Exception as e:
                logging.error(f"Attempt {attempt} failed: {str(e)}")
        
        if success:
            time.sleep(1)
            return True
                
        logging.error("Failed to reach checkout page after multiple attempts")
        return False
        
            
    except Exception as e:
        driver.save_screenshot("checkout_error.png")
        logging.error(f"Error during checkout: {e}")
        return False
    

# Main loop
while True:
    for url in PRODUCT_URLS:
        in_stock, product_name = check_product_and_get_name(url)
        if in_stock and product_name not in notified_products:
            # send_notification(url, product_name)
            checkout_url = add_to_cart(url)
            if checkout_url and checkout_url.startswith(BASE_CHECKOUT_URL):
                success = checkout(checkout_url, shipping_info, payment_info)
                if success:
                    logging.info("Checkout successful")
                    notified_products.add(product_name)
                    break
        else:
            logging.info(f"{product_name} is out of stock")

    if len(notified_products) == len(PRODUCT_URLS):
        logging.info("All products checked")
        break
    logging.info("Checking again...")
    logging.info("##############################################")
    time.sleep(5)



# def test_urls():
#     for url in PRODUCT_URLS:
#         inStock, product_name = check_product_and_get_name(url)
#         response = fetch_url(url)
#         soup = BeautifulSoup(response.content, 'html.parser')

#         # Find the "Add to Cart" button
#         add_to_cart_button = soup.find("button", class_="product-form__submit button button--primary")
#         button_text = add_to_cart_button.find("span").text.strip()

#         print(product_name)
#         print(button_text)
#         print(inStock)
#         print(url)
#         print("\n")

# test_urls()


# def test_add_to_cart():
#     for url in INSTOCK_URLS:
#         checkout_url = add_to_cart(url)
#         print(checkout_url)
#         print("\n")

# test_add_to_cart()

# def test_checkout():
#     shipping_info = {
#         'country': 'United Kingdom',
#         'email': 'darrensandhu01@gmail.com',
#         'first_name': 'Darren',
#         'last_name': 'Sandhu',
#         'address1': '14 Constance Avenue',
#         'address2': '',
#         'city': 'West Bromwich',
#         'postal_code': 'B70 6EF',
#         'phone': '07428117134'
#     }

#     payment_info = {
#         'name': 'Darren Sandhu',
#         'number': '5356 7401 1391 2604',
#         'expiry_month': '03',
#         'expiry_year': '27',
#         'cvv': '941'
#     }
    
#     url = "https://storeuk.taylorswift.com/products/the-tortured-poets-department-candle"
#     checkout_url = add_to_cart(url)
#     print('Ready to checkout:', checkout_url)
    
#     if checkout_url and checkout_url.startswith(BASE_CHECKOUT_URL):
#         success = checkout(checkout_url, shipping_info, payment_info)
#         print(f"Checkout {'successful' if success else 'failed'}")

# Repeat 20 times
# test_checkout()
    


# Switch to Dynamic Card Number iframe and fill in the card number
                    # card_number_iframe = WebDriverWait(driver, 15).until(
                    #     EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='card-fields-number-']"))
                    # )
                    # driver.switch_to.frame(card_number_iframe)
                    # logging.info("Switched to payment iframe")

                    # card_number_field = wait.until(EC.element_to_be_clickable((By.ID, "number")))
                    # if card_number_field:
                    #     card_number_field.send_keys(payment_info['number'])
                    #     if card_number_field.get_attribute("value") == payment_info['number']:
                    #         logging.info("Card number field filled correctly")
                    #     else:
                    #         logging.error("Card number field not filled correctly")
                    # else:
                    #     logging.error("Card number field not found")
                    

                    # # Switch to Dynamic Expiry iframe and fill in the expiry date
                    # driver.switch_to.default_content()
                    # card_expiry_iframe = WebDriverWait(driver, 15).until(
                    #     EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='card-fields-expiry-']"))
                    # )
                    # driver.switch_to.frame(card_expiry_iframe)

                    # card_expiry_field = wait.until(EC.element_to_be_clickable((By.ID, "expiry")))
                    # if card_expiry_field:
                    #     card_expiry_field.send_keys(payment_info['expiry_month'])
                    #     time.sleep(1)
                    #     card_expiry_field.send_keys(payment_info['expiry_year'])
                    #     logging.info("Card expiry field filled")
                    # else:
                    #     logging.error("Card expiry field not found")

                    # # Switch to Dynamic CVV iframe and fill in the CVV
                    # driver.switch_to.default_content()
                    # card_cvv_iframe = WebDriverWait(driver, 15).until(
                    #     EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='card-fields-verification_value-']"))
                    # )
                    # driver.switch_to.frame(card_cvv_iframe)
                    # card_cvv_field = driver.find_element(By.ID, "verification_value")
                    # if card_cvv_field:
                    #     card_cvv_field.send_keys(payment_info['cvv'])
                    #     logging.info("Card CVV field filled")
                    # else:
                    #     logging.error("Card CVV field not found")

                    #####################################################
                    #####################################################
                    #####################################################

                    # Switch back to default content
                    # Wait for email field to be present
                    # wait = WebDriverWait(driver, 10)
                    # email_field = wait.until(
                    #     EC.presence_of_element_located((By.ID, "email"))
                    # )
                    
                    # if email_field:
                    #     # Fill in shipping information
                    #     email_field.send_keys(shipping_info['email'])
                    #     logging.info("Email field filled")
                    
                    # #####################################################
                    # # Fill in the rest of the shipping information here #
                    # #####################################################
                    # country_field = driver.find_element(By.ID, "Select0")
                    # if country_field:
                    #     country_field.send_keys(shipping_info['country'])
                    #     logging.info("Country field filled")
                    #     time.sleep(1)
                    # else:    
                    #     logging.error("Country field not found")
                    
                    # first_name_field = driver.find_element(By.ID, "TextField0")
                    # if first_name_field:
                    #     first_name_field.send_keys(shipping_info['first_name'])
                    #     logging.info("First name field filled")
                    # else:
                    #     logging.error("First name field not found")

                    # last_name_field = driver.find_element(By.ID, "TextField1")
                    # if last_name_field:
                    #     last_name_field.send_keys(shipping_info['last_name'])
                    #     logging.info("Last name field filled")
                    # else:
                    #     logging.error("Last name field not found")
                    
                    # address1_field = driver.find_element(By.ID, "shipping-address1")
                    # if address1_field:
                    #     address1_field.send_keys(shipping_info['address1'])
                    #     logging.info("Address1 field filled")

                    #     # Wait for dropdown to appear
                    #     wait.until(EC.visibility_of_element_located((By.ID, "shipping-address1-options")))
                    #     logging.info("Dropdown loaded")

                    #     # Select first address from dropdown
                    #     shipping_address_aria = driver.find_element(By.ID, "shipping-address1-option-0")
                    #     shipping_address_aria.click()
                    #     logging.info("First address selected")
            
                    #     time.sleep(1)
                    # else:
                    #     logging.error("Address1 field not found")

                    # phone_field = driver.find_element(By.ID, "TextField5")
                    # if phone_field:
                    #     phone_field.send_keys(shipping_info['phone'])
                    #     logging.info("Phone field filled")
                    # else:
                    #     logging.error("Phone field not found")

                    #####################################################
                    #####################################################
                    #####################################################
