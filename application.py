from flask import Flask, redirect, request, render_template, flash

import json

import boto3

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'ac3b06a1-6db9-4e2a-b74a-ea24572ed710'

# Initialize the DynamoDB resource and specify the region
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

@app.route("/")
def home():
    return redirect("/login")

def read_all_entities(table_name):
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')

    # Get a reference to the DynamoDB table
    table = dynamodb.Table(table_name)

    try:
        # Use the scan method to read all items from the table
        response = table.scan()

        # Check if the scan was successful
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            # Return the list of items
            return response.get('Items', [])
        else:
            print("Error scanning the table.")
            return []
    except Exception as e:
        print("An error occurred:", e)
        return []

@app.route("/login", methods=["GET", "POST"])
def login():
    login_details = []  # Initialize an empty list for login details
    
    # Retrieve login details from DynamoDB
    table_name = 'Login'  # Replace with your table name
    login_details = read_all_entities(table_name)  # Get login details

    if request.method == "POST":
        provided_username = request.form.get("username")
        provided_password = request.form.get("password")
    
        for entity in login_details:
            if (
                provided_username == entity["user_name"] and
                provided_password == entity["password"]
            ):
                # Valid credentials, redirect to user-home page
                flash("Logged in")
                return redirect("/user-home")

        # Invalid credentials, show an error message
        flash("Invalid username or password")
    
    return render_template("login.html", login_details=login_details)

@app.route("/user-home")
def user_home():
    return render_template("user-home.html")

def create_login_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table_name = 'Login'
    table = dynamodb.Table(table_name)

    # Check if the table exists
    if table.table_status != 'ACTIVE':
        # Table doesn't exist, so create it
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'email',
                    'KeyType': 'HASH'  # Partition key
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        # Wait for the table to be created (this can take some time)
        table.wait_until_exists()
    
    return table


def generate_password(i):
    # Generate the password using a loop, similar to your old example
    return ''.join(str(j % 10) for j in range(i, i + 6))

def delete_all_logins(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('Login')

    # Use scan to get all items in the table
    response = table.scan()
    items = response.get('Items', [])

    # Delete each item
    for item in items:
        table.delete_item(Key={'email': item['email']})

def insert_initial_logins(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    # Delete all existing login entities
    delete_all_logins(dynamodb)

    table = dynamodb.Table('Login')
    for i in range(10):
        email = f"s3######{i}@student.rmit.edu.au"
        username = f"Firstname Lastname{i}"
        password = generate_password(i)

        item = {
            'email': email,
            'user_name': username,
            'password': password
        }
        
        table.put_item(Item=item)

# Define the table name and attributes
table_name = 'music'
table_attributes = [
    {
        'AttributeName': 'title',
        'AttributeType': 'S'
    },
    {
        'AttributeName': 'artist',
        'AttributeType': 'S'
    },
    {
        'AttributeName': 'year',
        'AttributeType': 'N'
    },
    {
        'AttributeName': 'web_url',
        'AttributeType': 'S'
    },
    {
        'AttributeName': 'image_url',
        'AttributeType': 'S'
    }
]

def table_exists(table_name):
    # Check if the table exists
    existing_tables = dynamodb.meta.client.list_tables()
    return table_name in existing_tables['TableNames']

def create_music_table():
    if not table_exists(table_name):
        try:
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'title',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'title',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            print(f'Table {table_name} has been created.')
        except Exception as e:
            print(f'Error creating table: {e}')
    else:
        print(f'Table {table_name} already exists. Skipping table creation.')

def load_data_to_table():
    # Check if the table already has data
    table = dynamodb.Table(table_name)
    if table.item_count > 0:
        print(f'Table {table_name} already has data. Skipping data loading.')
        return

    try:
        with open('a2.json', 'r') as json_file:
            data = json.load(json_file)
            songs = data.get('songs', [])  # Access the "songs" key in the JSON data

            for item in songs:
                table.put_item(Item=item)
            print(f'Data has been loaded into the {table_name} table.')
    except Exception as e:
        print(f'Error loading data: {e}')

from flask import Flask, redirect, request, render_template, flash

import json
import os
import requests
import boto3

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'ac3b06a1-6db9-4e2a-b74a-ea24572ed710'

# ... (Your existing code)

# Path to your a2.json file
json_file_path = 'a2.json'

# ... (Your existing code)

def image_exists_in_s3(s3, bucket_name, s3_object_key):
    try:
        # Attempt to head the S3 object (check for existence)
        s3.head_object(Bucket=bucket_name, Key=s3_object_key)
        return True
    except Exception as e:
        # An exception is raised if the object doesn't exist
        return False

def download_and_upload_images():
    # Load the JSON data
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    # Define the S3 bucket name
    bucket_name = '201c4962-cb1a-4775-9b92-889393597be0'


    s3 = boto3.client('s3', region_name='us-east-1')  # Replace 'us-east-1' with your desired region

    # Check if the S3 bucket exists, and create it if not
    if bucket_name not in [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]:
        s3.create_bucket(Bucket=bucket_name)

    # Directory to store downloaded images temporarily
    download_dir = 'downloaded_images'

    # Create the directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)

    # Loop through each song and upload the image to S3
    for song in data['songs']:
        image_url = song['img_url']
        artist_name = song['artist']

        # Generate a unique key for the S3 object using the artist's name
        s3_object_key = f'artists/{artist_name}.jpg'

        if image_exists_in_s3(s3, bucket_name, s3_object_key):
            print(f'Image for {artist_name} already exists in S3. Skipping.')
            continue

        # Download the image
        response = requests.get(image_url)

        if response.status_code == 200:
            # Save the downloaded image to the local directory
            image_path = os.path.join(download_dir, f'{artist_name}.jpg')
            with open(image_path, 'wb') as image_file:
                image_file.write(response.content)

            # Upload the image to S3
            s3.upload_file(image_path, bucket_name, s3_object_key)

            # Clean up: remove the local image file
            os.remove(image_path)

            print(f'Uploaded image for {artist_name} to S3.')

        else:
            print(f'Failed to download the image for {artist_name}.')

    print('Image upload to S3 completed.')

# ... (Your existing code)

if __name__ == '__main__':
    create_music_table()  # Create the DynamoDB table if it doesn't exist
    load_data_to_table()  # Load data from a2.json into the table if it's empty

    download_and_upload_images()  # Download and upload artist images to S3

    app.run(host='0.0.0.0')
