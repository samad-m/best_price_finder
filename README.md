# Amazon Best Price Finder (BPF) #

## Motivation ##
The Amazon Best Price Finder (BPF) is a Flask app I created to make shopping on Amazon fast and simple. Amazon search results often contain product styles that look similar but are sold at different price points. This is a result of Amazon's Marketplace platform; different sellers import the same products and sell them through their respective storefronts. It's common to see identical products being sold under a plethora of product titles, descriptions, and price points. Search results are messy and make price-conscious shopping a pain.

> __For example:__
>
> These are the search results for the product I want. It's mainly comprised of things I don't care for.
> ![Search Results](https://i.imgur.com/vbtiagG.png) 
>
> This is a product I like!
> ![Example 1](https://i.imgur.com/R59lVhT.png)
>
> Oh - hey! The same product style at a different price!
> ![Example 2](https://i.imgur.com/rpOvq1g.png)
>
> And another one?! How can I find the cheapest version of this product?
> ![Example 3](https://i.imgur.com/GOvhr4Z.png)

I was tired of sifting through search results for the lowest price on the products I wanted. Hence, the BPF was born!

## Functional Description ##
At the top-level, the Flask app performs the following functionality:

> The user inputs the URL of an Amazon product they like, and the BPF returns a table containing the most similar-looking products, sorted by ascending price. 

The BPF can be broken down into two functional blocks:

### 1. Data Collection ###
Requests and BeautifulSoup are used to handle the data collection of the Amazon search results.

- The search keyword the user used can be extracted from the input URL. Using the search keyword, Requests performs a live-query on Amazon.

- BeautifulSoup is used in order to download product information (product image, title, rating, price, and URL). This is performed for the user's input product, and all the queried Amazon search results.

### 2. Neural Network ###
By comparing product images' feature vectors, the most similar product images to the user's input can be found.

- The Keras front end is used with the TensorFlow back end in order to process the images. For superior speed and generalization, the pre-trained VGG16 Convolutional Neural Network (CNN) is utilized.

__VGG16__
![vgg16](https://neurohive.io/wp-content/uploads/2018/11/vgg16-1-e1542731207177.png)

- All product images are input to the VGG16 model. Rather than classifying images, my goal is to obtain feature vectors, and so the fully-connected layers are stripped from the end of VGG16. The output is a unique feature vector for every product image input.

- Cosine similarity is used as a metric to calculate similarity between feature vectors. By calculating the similarity between the user's input product and every Amazon search result, the most similar products can be found.

__Cosine Similarity Formula__
![similarity](https://www.machinelearningplus.com/wp-content/uploads/2018/10/Cosine-Similarity-Formula-1.png)

- The user can enter the _n_ number of products to compare the input product to. A table containing the _n_ most similar products is returned, in order of ascending price.

## Directory Structure ##
1. `flask_app` contains all the necessary code to run the BPF
    - `app.py` is the main file that must be run to start the program
    - `imports.py` contains the bulk of the function definitions used in `app.py`
    - `static` and `templates` are used for the Flask HTML/CSS front end
    - `data/data` is where scraped images are temporarily stored
2. `notebooks` contains the Jupter notebooks used during development. The Data Collection and Neural Network blocks are split into separate notebooks. Outside of the code organization, these two notebook files are functionally equivalent to the `.py` files in `flask_app`

## Future Work ##
1. Debug HTML scraper for updated Amazon list-view HTML
    - Amazon recently updated the HTML for list-view search results, breaking the current scraper. Currently, the scraper works correctly for grid-view search results
2. Host Flask app in the cloud 