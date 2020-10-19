import datetime
import json
import re

import boto3
import requests

# Probably not great to commit this, but this is a quick script and I don't want to deal with properly securing it.
TRACKING_NUMBERS = [
    "60058350",  # Chairs
    "60058351",
    "60058352",
    "60058353",
    "60058354",
    "60058355",
    "60058356",  # Tables
    "60058357"  # Rug
]

ENDPOINT = "https://www.westelm.com/customer-service/order-tracking/index.json?carrier=WSI&trackingNumber="


def handler(event, context):
    updated_responses = []
    for tracking_number in TRACKING_NUMBERS:
        print(tracking_number)
        url = ENDPOINT + tracking_number
        response = requests.get(url)
        response_json = response.json()
        print(response_json)

        activities = response_json["trackingDetailBean"]["activityList"]
        activity_times = map(
            lambda activity: time_string_to_datetime(activity["activityDate"]),
            activities)

        sorted_activity_times = sorted(activity_times)

        last_update = sorted_activity_times[-1]
        now = datetime.datetime.now()

        delta = now - last_update

        if delta.minute > 55:
            updated_responses.append(response_json)

    print(updated_responses)
    notify(updated_responses)


def notify(content):
    client = boto3.client('sns')
    response = client.publish(
        TopicArn='arn:aws:sns:us-east-1:692594597524:WestElmShippingNotifications:bbedad87-1725-4b55-a180-6a3fb1c35b1a',
        Message=json.dump(content),
        Subject='West Elm Shipping Notification',
        MessageStructure='string',
    )
    print(response)


def time_string_to_datetime(time_string):
    result = re.search(
        "([A-Za-z]+)\. ([0-9]{1,2}), ([0-9]{4}) ([0-9]{1,2}):([0-9]{2}) (AM|PM)",
        time_string)
    month = abbreviation_to_month(result.group(1))
    day = result.group(2)
    year = result.group(3)
    hour = result.group(4)
    minute = result.group(5)
    am_pm = result.group(6)

    if am_pm == "PM":
        hour += 12

    return datetime.datetime(year, month, day, hour, minute)


def abbreviation_to_month(abbreviation):
    if abbreviation == "Oct":
        return "10"
    if abbreviation == "Nov":
        return "11"
    raise NotImplementedError
