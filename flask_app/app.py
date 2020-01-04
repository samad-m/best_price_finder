from flask import Flask, render_template, url_for, request

import pandas as pd
import numpy as np

from keras.applications.vgg16 import VGG16  # Pre-trained model
from keras.applications.imagenet_utils import decode_predictions
from keras.utils import np_utils
from keras.layers import Dense, Conv2D, MaxPooling2D, Flatten
from keras.models import Model
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img

from sklearn.metrics.pairwise import cosine_similarity

from imports import *

app = Flask(__name__)

def get_results(url, num_listings):
    # Extract search keywords from URL
    search_keyword = get_search_keyword(url)

    # Extract product name from URL
    input_product = get_product_name(url)

    # Create DF containing all the products from first 20 pages of
    # Amazon search results
    df = create_product_df(search_keyword)

    # Drop the listings with duplicate entries
    df.drop_duplicates(subset=['name'], inplace=True)

    # Reset index
    df.reset_index(drop=True, inplace=True)

    # Index of input image
    # This image will be compared to every other image
    input_index = df[df.name == input_product].index[0]

    # Download all the product images to /data/data
    get_product_images(df)

    # Initialize model
    # Exclude the final dense layers by setting include_top=False
    # Input images need to be 224x224 with 3 color channels (RGB) 
    model = VGG16(weights='imagenet', include_top=False, input_shape=(224,224,3)) 

    # Loading all the images as a np array
    # The images have to be in a subdirectory, i.e. they're in pwd/data/data
    # shuffle=False to keep images in correct number order
    # The target_size is (224,224) so they fit into the input_shape of the VGG16 model
    # The target_size resizes our image to 224x224
    # We aren't doing classification, so class_mode=None
    images_array = ImageDataGenerator().flow_from_directory('data', shuffle=False, target_size=(224,224), class_mode=None)

    # Put array of images thru dissected VGG16 model to obtain array of feature embeddings
    # Number of images
    num_images = len(images_array.filenames)

    # .reshape(num_images,-1) to flatten the images into num_images rows, one for each image
    # There are num_images images (rows), and -1 automatically creates the correct number of 
    # columns (features)
    prediction_array = model.predict_generator(images_array).reshape(num_images,-1)

    # Create similarities column in df
    # Each image will containe its cosine similarity to the input_index image
    similarities = []

    for product in range(num_images):
        similarities.append(float(cosine_similarity(prediction_array[input_index].reshape(1,-1), prediction_array[product].reshape(1,-1))))

    # Add similarities column to df
    df['similarities'] = similarities

    # Delete all the downloaded images
    delete_product_images(df)

    # Create separate df for input image
    # Currently unused
    # input_image_df = df.iloc[input_index,:]

    # Drop input image from original df
    # Doing this because we don't want to recommend the product the user inputs
    df.drop(input_index, inplace=True)

    # Sort by descending similarity value
    df.sort_values(by='similarities', ascending=False, inplace=True)

    # Prevent displayed data from being truncated
    pd.set_option('display.max_colwidth', -1)

    # Drop any rows that have np.nan in price or rating
    df.dropna(inplace=True, subset=['price', 'rating'])

    # Filter down to the number of listings the user wants to see, sorted by $-$$
    df = df.iloc[:num_listings,1:].sort_values(by='price')

    # Create new column which will contain product names, with hyperlinks to product page
    df['product'] = df['name'] + '###' + df['url'] 

    # Keep only necessary columns
    df = df[['product', 'rating', 'price']]

    df.rename(columns={'product': 'Product', 'rating': 'Rating', 'price': 'Price'}, inplace=True)

    # Return df, where Product column has hyperlink items
    return df.style.format({'Product': make_clickable_both}).hide_index().render()

# Following two functions are to prevent web browser from caching
# Without this, updating the CSS doesn't properly update HTML render
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

# Decorator to interface between HTML I/O and Python backend
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':                                      # If the user hits submit, this data is extracted
        input_url = request.form['input_url']                         # URL of input product
        input_num_listings = int(request.form['input_num_listings'])  # Number of listings to show

        df = get_results(input_url, input_num_listings)               # Pass user input data and run get_results function

        return render_template('index.html', df=df)                   # Print out table containing most similar products
    
    else:
        return render_template('index.html')                          # No action is taken; render HTML

# debug=False when trying to run the application
# debug=True when making changes to the app, and want to see the changes live
# threaded=False because a Keras bug gives an error when it's True 
if __name__ == '__main__':
    app.run(debug=False, threaded=False)