import datetime
import httpx
import math
import os
import json
import argparse
from dotenv import load_dotenv

# parse the commandline argument if passed
parser = argparse.ArgumentParser()
parser.add_argument("--env_file", default="staging",
                    help="Please Specify .env file name")
args = parser.parse_args()

env_path = f"env/.env.{args.env_file}"
env_file = os.getenv("ENV_FILE", "staging")

load_dotenv(env_path)

# variables
path_to_admin_token = 'env/admin_token.json'
path_to_user_token = 'env/user_token.json'
path_to_user_json = 'setUp/users.json'


with open(path_to_user_json, 'r') as file:
    user_json = json.load(file)

user_details = user_json['staging'] if args.env_file == 'staging' else user_json['prod']

user_email_list: list[str] = [item['user_email'] for item in user_details]
print(user_email_list)


def _setTokenObject(access_token, id_token):
    currentTimeWhenWeReceiveTheToken = math.floor(
        datetime.datetime.now().timestamp())
    eightHoursLaterWhenTokenExpires = currentTimeWhenWeReceiveTheToken + \
        (8 * 60 * 60)
    tokenObject = {
        "access_token": access_token,
        "id_token": id_token,
        "expiration_date": eightHoursLaterWhenTokenExpires
    }
    return tokenObject


async def setUpAdminToken():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    payload = {
        "grant_type": os.getenv("GRANT_TYPE"),
        "username": os.getenv("AUTH0_ADMIN_USERNAME"),
        "password": os.getenv("AUTH0_ADMIN_PASSWORD"),
        "audience": os.getenv("AUDIENCE"),
        "scope": os.getenv("SCOPE"),
        "client_id": os.getenv("AUTH0_CLIENT_ID"),
        "realm": os.getenv("REALM"),
    }
    auth_url = os.getenv("AUTH0_USER_TOKEN_URL")
    sampleAdminTokenObject = {
        "access_token": '',
        "id_token": '',
        "expiration_date": 1588291200  # May 1, 2020
    }

    if os.path.exists(path_to_admin_token):
        if os.path.getsize(path_to_admin_token) == 0:
            with open(path_to_admin_token, "w") as file:
                json.dump(sampleAdminTokenObject, file)
        with open(path_to_admin_token, 'r') as file:
            data = json.load(file)
            sampleAdminTokenObject["access_token"] = data["access_token"]
            sampleAdminTokenObject["id_token"] = data["id_token"]
            sampleAdminTokenObject["expiration_date"] = data["expiration_date"]

    currentTimeInSeconds = math.floor(datetime.datetime.now().timestamp())

    if not os.path.exists(path_to_admin_token) or sampleAdminTokenObject["expiration_date"] < currentTimeInSeconds:
        print("Fetching Admin Token Now")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url=auth_url, headers=headers, data=payload)
                json_data_from_response = response.json()
                access_token = json_data_from_response["access_token"]
                id_token = json_data_from_response["id_token"]
                token_object = _setTokenObject(
                    access_token=access_token, id_token=id_token)
                with open(path_to_admin_token, 'w') as file:
                    json.dump(token_object, file)
        except Exception as e:
            print(f"An error occured on setAdminToken: {e}")
    else:
        print("Admin token has not expired yet.")


async def setUpUserToken():
    sample_user_token_dict = [{
        "user_email": {
            "access_token": '',
            "id_token": '',
            "expiration_date": 00000,
        },
    }]
    first_user_token = sample_user_token_dict[0]
    expiration_time_for_user_token = sample_user_token_dict[0]["user_email"]["expiration_date"]

    if os.path.exists(path_to_user_token):
        if os.path.getsize(path_to_user_token) == 0:
            with open(path_to_user_token, "w") as file:
                json.dump(sample_user_token_dict, file)
        with open(path_to_user_token, 'r') as file:
            data = json.load(file)
            first_user_token = data[0]
            for key in first_user_token:
                if "expiration_date" in first_user_token[key]:
                    expiration_time_for_user_token = first_user_token[key]["expiration_date"]

    current_time_in_seconds = math.floor(datetime.datetime.now().timestamp())

    if not os.path.exists(path_to_user_token) or expiration_time_for_user_token < current_time_in_seconds:
        token_for_all_users = []
        for email in user_email_list:
            payload = {
                "audience": os.getenv("AUDIENCE"),
                "client_id": os.getenv("AUTH0_CLIENT_ID"),
                "grant_type": os.getenv("GRANT_TYPE"),
                "username": email,                "password": os.getenv("USER_PASSWORD"),
                "realm": os.getenv("REALM"),
                "scope": os.getenv("SCOPE"),
            }
            headers = {
                "Content-Type": "application/json"
            }
            user_auth_url = os.getenv("AUTH0_USER_TOKEN_URL")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url=user_auth_url, json=payload, headers=headers)
                    json_data_from_response = response.json()
                    access_token = json_data_from_response["access_token"]
                    id_token = json_data_from_response["id_token"]
                    token_object = _setTokenObject(
                        access_token=access_token, id_token=id_token)
                    single_user_token_object = {
                        email: token_object
                    }
                    token_for_all_users.append(single_user_token_object)
            except Exception as e:
                print(f"An error occurred on set_user_token: {e}")

        with open(path_to_user_token, 'w') as file:
            json.dump(token_for_all_users, file)
    else:
        print("User token has not exipred yet.")
