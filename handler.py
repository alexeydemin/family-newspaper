import pdfkit
import boto3
import os
from botocore.vendored import requests
import random

client = boto3.client('s3')

# Get the bucket name environment variables to use in our code
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
api_url = 'https://api.telegram.org/bot1326583594:AAHT8mP2wDnCtg5DgDGvZhpYLObzlIRssww/'
api_file_url = 'https://api.telegram.org/file/bot1326583594:AAHT8mP2wDnCtg5DgDGvZhpYLObzlIRssww/'


def get_photo_by_id(id):
    r = requests.get(api_url + 'getFile?file_id=' + id)
    return api_file_url + r.json()['result']['file_path']


def get_posts(event, context):
    r = requests.get(api_url + 'getUpdates')
    response = []
    for post in r.json()['result']:
        text = ''
        photo = ''
        if 'message' in post:
            message = post['message']
            if 'text' in message:
                text = message['text']
            if 'photo' in message:
                photo = get_photo_by_id(message['photo'][0]['file_id'])
            if 'caption' in message:
                text = message['caption']
            response.append({'photo': photo, 'text': text})

    return response


def generate_html(event, context):
    html = '<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><style> div {border-radius: 15px; background-color: #6497b1; width:100%; height:100%;padding: 15px;}</style></head><body><table cellspacing="40" cellpadding="0" width=100% height="100%"><tr>'
    for i, post in enumerate(event):
        colors = ['4a4e4d', '0e9aa7','3da4ab', 'f6cd61', 'fe8a71']
        html += '<td><div style="background-color: #' + random.choice(colors) + '">'
        if post['photo']:
            html += '<img src=' + post['photo'] + '>'
        if post['text']:
            html += post['text']
        html += '</div></td>'
        if (i + 1) % 3 == 0:
            html += '</tr><tr>'
    html += '</tr></table></body></html>'

    return {
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "statusCode": 200,
        "body": html
    }


def generate_pdf(event, context):
    # Defaults
    key = 'default-filename.pdf'
    html = "<html><head></head><body><h1>It works! This is the default PDF.</h1></body></html>"

    # Decode json and set values for our pdf
    if 'body' in event:
        html = event['body']
        key = 'default-filename.pdf'

    # Set file path to save pdf on lambda first (temporary storage)
    filepath = '/tmp/{key}'.format(key=key)

    # Create PDF
    # Download https://wkhtmltopdf.org/downloads.html and put it to binary directory
    config = pdfkit.configuration(wkhtmltopdf="binary/wkhtmltopdf")    
    pdfkit.from_string(html, filepath, configuration=config, options={})

    # Upload to S3 Bucket
    r = client.put_object(
        ACL='public-read',
        Body=open(filepath, 'rb'),
        ContentType='application/pdf',
        Bucket=S3_BUCKET_NAME,
        Key=key
    )

    return {
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "statusCode": 200,
        "body": "https://{0}.s3.amazonaws.com/{1}".format(S3_BUCKET_NAME, key)
    }
