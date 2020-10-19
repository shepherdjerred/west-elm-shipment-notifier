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
    last_updates = []
    for tracking_number in TRACKING_NUMBERS:
        url = ENDPOINT + tracking_number
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
        }
        response = requests.get(url, headers=headers)
        print(response.content)
        response_json = json.loads(response.content)
        print(response_json)

        activities = response_json["trackingDetailBean"]["activityList"]
        activity_times = map(
            lambda activity: time_string_to_datetime(activity["activityDate"]),
            activities)

        sorted_activity_times = sorted(activity_times)

        last_update = sorted_activity_times[-1]
        last_updates.append(last_update)
        print(last_update)

        now = datetime.datetime.now()

        delta = now - last_update

        print(delta)

        if delta.total_seconds() / 60 < 40:
            updated_responses.append(response_json)

    print(f"Last updates: {sorted(last_updates)}")
    print(f"Updates: {updated_responses}")

    if len(updated_responses) > 0:
        notify(updated_responses)


def notify(content):
    client = boto3.client('sns')
    response = client.publish(
        TopicArn='arn:aws:sns:us-east-1:692594597524:WestElmShipmentNotifications',
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
    day = int(result.group(2))
    year = int(result.group(3))
    hour = int(result.group(4))
    minute = int(result.group(5))
    am_pm = result.group(6)

    if am_pm == "PM":
        hour += 12

    return datetime.datetime(year, month, day, hour, minute)


def abbreviation_to_month(abbreviation):
    if abbreviation == "Oct":
        return 10
    if abbreviation == "Nov":
        return 11
    raise NotImplementedError

handler(None, None)
