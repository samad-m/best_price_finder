import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from fake_useragent import UserAgent  # To spoof user-agent when doing requests
import urllib.request  # To download images
import os  # To download images to /data/data directory and to 
           # delete images once they are not being used

# Functions to extract info from input URL

# Given URL, output the search keywords that were used
def get_search_keyword(url):
    return url.split('keywords=')[1].split('&')[0]

# Given URL, output the name of the product on the page
def get_product_name(url):
    # What Amazon sees when we do the request
    headers = {'User-Agent': UserAgent().random,  # Use random user agent
               "Accept-Encoding":"gzip, deflate", 
               "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
               "DNT":"1","Connection":"close", 
               "Upgrade-Insecure-Requests":"1"}
    
    # Create request for url
    r = requests.get(url, headers=headers)
    content = r.content
    
    # Create BeautifulSoup object from HTML code
    soup = BeautifulSoup(content)
    
    # Return the product name, removed of whitespace
    return soup.find('span', attrs={'id': 'productTitle'}).text.strip()



# Functions to format text

# Given an HTML snippet, return the formatted text 
def get_text(series): 
    try:
        return series.text
    except:
        return np.nan

# Remove newline characters from start and end of ratings
# Remove 'out of 5 stars'
# If a product doesn't have a rating, set it to np.nan
def clean_rating(series):
    try:
        return float(series.lstrip('\n\n').rstrip('\n\n out of 5 stars'))
    except:
        return np.nan

# Remove dollar sign ($) from price and convert value to float
# If a product doesn't have a price, set it to np.nan
def clean_price(series):
    try:
        return float(series.lstrip('$'))
    except:
        return np.nan



# Function to create a DF (for a single search result page)

# Given page number and search keyword, return a DF containing:
# Product name, page, price, image url, rating, and url
def get_product_details(page_num, search_keyword):
    # What Amazon sees when we do the request
    headers = {'User-Agent': UserAgent().random,  # Use random user agent
               "Accept-Encoding":"gzip, deflate", 
               "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
               "DNT":"1","Connection":"close", 
               "Upgrade-Insecure-Requests":"1"}
    
    # Replace whitespace with + so that it can be used for searching
    search_keyword = search_keyword.replace(' ', '+')
    
    # Create URL
    url = "https://www.amazon.com/s?k={}&page={}".format(str(search_keyword), str(page_num))
    print(url)
    
    # Create request for url
    r = requests.get(url, headers=headers)
    content = r.content
    
    # Create BeautifulSoup object from HTML code
    soup = BeautifulSoup(content)
    
    # Check if the search result is list or grid view
    list_view_check = soup.find('div', attrs={'class': 'sg-col-20-of-24 s-result-item sg-col-0-of-12 sg-col-28-of-32 sg-col-16-of-20 sg-col sg-col-32-of-36 sg-col-12-of-16 sg-col-24-of-28'})
    
    if list_view_check:
        search_mode = 'list'
        products_on_page = soup.findAll('div', attrs={'class': 's-include-content-margin s-border-bottom'})  # Contains all products on page
    elif not list_view_check:
        search_mode = 'grid'
        products_on_page = (soup.findAll('div', attrs={'class': 's-expand-height s-include-content-margin s-border-bottom'}))  # Contains all products on page
    
    # Create list of dicts to store info
    data = []
    
    if search_mode == 'list':  # Search results load in list view format
        # Iterate thru the products on the page
        for product in products_on_page:
            # Create dict to store product info
            product_dict = {}

            # Get product information 
            product_details = product.find('div', attrs={'class': 'sg-col-4-of-12 sg-col-8-of-16 sg-col-16-of-24 sg-col-12-of-20 sg-col-24-of-32 sg-col sg-col-28-of-36 sg-col-20-of-28'})

            # Get product URL, name, page, price, and rating
            product_dict['url'] = 'https://amazon.com' + product_details.find('a', attrs={'class': 'a-link-normal a-text-normal'})['href']
            product_dict['name'] = product_details.find('span', attrs={'class': 'a-size-medium a-color-base a-text-normal'})
            product_dict['page'] = page_num
            product_dict['price'] = product_details.find('span', attrs={'class': 'a-offscreen'})
            
            # Some products do not have ratings
            try: 
                product_dict['rating'] = product_details.find('span', attrs={'class': 'a-icon-alt'})
            except:
                product_dict['rating'] = np.nan

            # Get product image
            product_dict['image_url'] = product.find('div', attrs = {'class': 'a-section aok-relative s-image-fixed-height'}).find('img')['src']

            # Add product_dict to our list of dicts
            data.append(product_dict)
            
    elif search_mode == 'grid':  # Search results load in grid view format
        # Iterate thru the products on the page
        for product in products_on_page:
            # Create dict to store product info
            product_dict = {}

            # Get product information 
            product_details = product.findAll('div', attrs={'class': 'sg-row'})[-1]

            # Get product URL, name, page, price, and rating
            product_dict['url'] = 'https://amazon.com' + product_details.find('a', attrs={'class': 'a-link-normal a-text-normal'})['href']
            product_dict['name'] = product_details.find('span', attrs={'class': 'a-size-base-plus a-color-base a-text-normal'})
            product_dict['page'] = page_num

            # Some products do not have prices
            try: 
                product_dict['price'] = product_details.find('span', attrs={'class': 'a-offscreen'})
            except:
                product_dict['price'] = np.nan 
            
            # Some products do not have ratings
            try: 
                product_dict['rating'] = product_details.find('div', attrs={'class': 'a-row a-size-small'}).find('span')
            except:
                product_dict['rating'] = np.nan

            # Get product image
            product_dict['image_url'] = product_details.find('div', attrs = {'class': 'a-section aok-relative s-image-square-aspect'}).find('img')['src']

            # Add product_dict to our list of dicts
            data.append(product_dict)
    
    # DF containing all our data
    df = pd.DataFrame(data)
    
    # Given HTML strings, update them to formatted text
    df.name = df.name.apply(get_text)
    
    df.price = df.price.apply(get_text)
    df.price = df.price.apply(clean_price)  # Remove $ signs, convert to float
    
    df.rating = df.rating.apply(get_text)
    df.rating = df.rating.apply(clean_rating)  # Remove 'out of 5 stars' and whitestpace, convert to float
    
    return df



# Function to create DF (for all pages)

# Given a search keyword, return a DF containing all products on the
# search's first 20 pages (Amazon's limit) 
def create_product_df(search_keyword):
    # Create DF to store info
    df = pd.DataFrame()

    # Iterate thru all 20 pages
    # Amazon only lets you go thru 20 pages
    for page in range(1, 21):
        page_df = get_product_details(page, search_keyword)

        # Append DF from page to our master df
        df = df.append(page_df, ignore_index=True)
        
    return df



# Functions to download/delete images

# Download image for all the products into the current directory
def get_product_images(df):
    
    # Get the digits place so that we can do left-zero padding
    # e.g. 123 will have digits_places=3
    # Do left-zero padding for Keras alhanumeric sorting
    # e.g. to prevent sorting as 1, 10, 100, etc.
    digits_places = len(str(len(df)))
    
    # Iterate thru the all the image URLs
    for index, url in df.image_url.iteritems():
        
        # Convert int to str
        index_str = str(index)

        # Construct filename of the downloaded image
        # Includes the directory where the image is to be stored
        # zfill pads the left of the string, such that the total number of digits
        # is equal to digits_places
        full_filename = os.path.join(os.getcwd() + '/data/data/', index_str.zfill(digits_places) + '.jpg')
        
        # Download image
        urllib.request.urlretrieve(url, full_filename)

# Delete images for all the products from the current directory
def delete_product_images(df):
    
    # Get the digits place so that we can do left-zero padding
    # e.g. 123 will have digits_places=3
    # Do left-zero padding for Keras alhanumeric sorting
    # e.g. to prevent sorting as 1, 10, 100, etc.
    digits_places = len(str(len(df)))
    
    # Iterate thru the all the images
    for index in range(len(df)):
        
        # Convert int to str
        index_str = str(index)

        # Construct filename of the downloaded image
        # Includes the directory where the image is to be stored
        # zfill pads the left of the string, such that the total number of digits
        # is equal to digits_places
        full_filename = os.path.join(os.getcwd() + '/data/data/', index_str.zfill(digits_places) + '.jpg')
        
        # Delete image
        os.remove(full_filename)



# Function to make display hyperlinks

# Input is the string url+name and turns it into a hyperlink
# Output is a link where the visible name is the product name, 
# and the hyperlink is the product link
def make_clickable_both(val): 
    name, url = val.split('###') 
    return f'<a href="{url}">{name}</a>'