import boto3
from botocore.exceptions import ClientError
import urllib.parse
import os
import io
from PIL import Image
from io import BytesIO
import os
import re

import boto3


def send_email(subject, body, recipient, sender):
    AWS_REGION = "ap-south-1"
    CHARSET = "UTF-8"

    client = boto3.client("ses", region_name=AWS_REGION)

    response = client.send_email(
        Destination={
            "ToAddresses": [
                recipient,
            ],
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": CHARSET,
                    "Data": body,
                },
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": subject,
            },
        },
        Source=sender,
    )

    return response


s3_client = boto3.client("s3")


def lambda_handler(event, context):
    # Get the S3 object key from the event
    key = event["Records"][0]["s3"]["object"]["key"]
    # Get the S3 bucket name from the event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    # Get the S3 bucket size from the event
    size = event["Records"][0]["s3"]["object"]["size"]
    # print the bucket name and file name
    S3_URI = "s3://{}/{}".format(bucket, key)
    print("BUCKET NAME : " + bucket + "  ")
    print("OBJECT NAME : " + key + "  ")
    print("SIZE OF OBJECT  : %d" % size)

    # Get the object metadata from S3
    response = s3_client.head_object(Bucket=bucket, Key=key)
    object_size = response["ContentLength"]
    object_type = response["ContentType"]

    # Check if the object is an image
    if object_type.startswith("image/"):
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        with Image.open(obj["Body"]) as img:
            # Generate a thumbnail of the original image
            img.thumbnail((100, 100))
            orig_size = obj["ContentLength"]
            thumb_size = img.size
            print("Original File: {} ({} bytes)".format(key, orig_size))
            thumb_key = "thumbnails/" + os.path.basename(key)
            S3_Thumb_URI = "s3://{}/{}".format(bucket, thumb_key)
            thumb_F_size = thumb_size[0] * thumb_size[1] * 3
            print(
                "Thumbnail: {} ({} bytes)".format(
                    thumb_key, thumb_size[0] * thumb_size[1] * 3
                )
            )
            #upload thumbnail into s3
            s3_client.put_object(
                Bucket=bucket,
                Key=thumb_key,
                Body=img.tobytes(),
                ContentType="image/jpeg",
            )
            # email subject and text manipulation
        subject = "Email from Lambda for the files which are Images"
        body = (
            "Hello \r\n"
            "This email was sent from a Lambda function with the details of images and its Thumbnail.\r\n"
            "Below are the details:\r\n"
            "S3_URI: " + S3_URI + "  \n"
            "BUCKET NAME: " + bucket + " \n"
            "ORIG_F_NAME: " + key + "  \n"
            "SIZE OF IMAGE: %d" % size + "\n"
            "THUMBNAIL_FILE_NAME: " + thumb_key + "  \n"
            "SIZE_OF_THUMBNAIL: %s" % thumb_F_size + "\n"
            "S3_URI_THUMBNAILS: " + S3_Thumb_URI + "  \n"
        )

        recipient = "2022MT93589@wilp.bits-pilani.ac.in"
        sender = "2022MT93589@wilp.bits-pilani.ac.in"
        # Call email fuction
        response = send_email(subject, body, recipient, sender)
        print(response)
    else:
        # updating the body of the email for non image image file
        subject = "Email from Lambda for the files which are not Images"
        body = (
            "Hello \r\n"
            "This email was sent from a Lambda function with the details of file which are not images.\r\n"
            "Below the datails:\r\n"
            "S3_URI : " + S3_URI + "  \n"
            "BUCKET NAME : " + bucket + " \n "
            "OBJECT_NAME : " + key + "  \n"
            "SIZE_OF_OBJECT  : %d" % size
        )
        # add your email address in recipient and sender enclosed with double quots", use the email whcih you setup in AWS SES
        recipient = "2022MT93589@wilp.bits-pilani.ac.in"
        sender = "2022MT93589@wilp.bits-pilani.ac.in"
        # Call email fuction
        response = send_email(subject, body, recipient, sender)
        print(response)