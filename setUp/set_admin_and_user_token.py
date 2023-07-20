""" This is sample test"""
import argparse
import datetime
import json
import os
import math
import httpx
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
PATH_TO_ADMIN_TOKEN = 'env/admin_token.json'
PATH_TO_USER_TOKEN = 'env/user_token.json'
PATH_TO_USER_JSON = 'setUp/users.json'


with open(PATH_TO_USER_JSON, 'r', encoding='utf-8') as file:
    user_json = json.load(file)

user_details = user_json['staging'] if args.env_file == 'staging' else user_json['prod']

user_email_list: list[str] = [item['user_email'] for item in user_details]
print(user_email_list)


def _set_token_object(access_token, id_token):
    current_time_when_we_receive_token = math.floor(
        datetime.datetime.now().timestamp())
    eight_hours_later_when_token_expires = current_time_when_we_receive_token + \
        (8 * 60 * 60)
    token_object = {
        "access_token": access_token,
        "id_token": id_token,
        "expiration_date": eight_hours_later_when_token_expires
    }
    return token_object


async def set_up_admin_token():
    """Writes Admin Token to env folder so all api tests can use them"""
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
    admin_token = {
        "access_token": '',
        "id_token": '',
        "expiration_date": 1588291200  # May 1, 2020
    }

    if os.path.exists(PATH_TO_ADMIN_TOKEN):
        if os.path.getsize(PATH_TO_ADMIN_TOKEN) == 0:
            with open(PATH_TO_ADMIN_TOKEN, "w", encoding='utf-8') as admin_token_file:
                json.dump(admin_token, admin_token_file)
        with open(PATH_TO_ADMIN_TOKEN, 'r', encoding='utf-8') as admin_token_file:
            data = json.load(admin_token_file)
            admin_token["access_token"] = data["access_token"]
            admin_token["id_token"] = data["id_token"]
            admin_token["expiration_date"] = data["expiration_date"]

    current_time = math.floor(datetime.datetime.now().timestamp())

    if not os.path.exists(
            PATH_TO_ADMIN_TOKEN) or admin_token["expiration_date"] < current_time:
        print("Fetching Admin Token Now")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url=auth_url, headers=headers, data=payload)
                json_data_from_response = response.json()
                access_token = json_data_from_response["access_token"]
                id_token = json_data_from_response["id_token"]
                token_object = _set_token_object(
                    access_token=access_token, id_token=id_token)
                with open(PATH_TO_ADMIN_TOKEN, 'w', encoding='utf-8') as admin_token_file:
                    json.dump(token_object, admin_token_file)
        except (httpx.HTTPError) as error:
            print(f"An error occured on setAdminToken: {error}")
    else:
        print("Admin token has not expired yet.")


async def set_up_user_token():
    """For Each User listed in teh env folder, this gets user token and saves"""
    sample_user_token_dict = [{
        "user_email": {
            "access_token": '',
            "id_token": '',
            "expiration_date": 00000,
        },
    }]
    first_user_token = sample_user_token_dict[0]
    expiration_time_for_user_token = sample_user_token_dict[0]["user_email"]["expiration_date"]

    if os.path.exists(PATH_TO_USER_TOKEN):
        if os.path.getsize(PATH_TO_USER_TOKEN) == 0:
            with open(PATH_TO_USER_TOKEN, "w", encoding='utf-8') as user_token_file:
                json.dump(sample_user_token_dict, user_token_file)
        with open(PATH_TO_USER_TOKEN, 'r', encoding='utf-8') as user_token_file:
            data = json.load(user_token_file)
            first_user_token = data[0]
            for key in first_user_token:
                if "expiration_date" in first_user_token[key]:
                    expiration_time_for_user_token = first_user_token[key]["expiration_date"]

    current_time = math.floor(datetime.datetime.now().timestamp())

    if not os.path.exists(
            PATH_TO_USER_TOKEN) or expiration_time_for_user_token < current_time:
        token_for_all_users = []
        for email in user_email_list:
            payload = {
                "audience": os.getenv("AUDIENCE"),
                "client_id": os.getenv("AUTH0_CLIENT_ID"),
                "grant_type": os.getenv("GRANT_TYPE"),
                "username": email, "password": os.getenv("USER_PASSWORD"),
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
                    token_object = _set_token_object(
                        access_token=access_token, id_token=id_token)
                    single_user_token_object = {
                        email: token_object
                    }
                    token_for_all_users.append(single_user_token_object)
            except httpx.HTTPError as error:
                print(f"An error occurred on set_user_token: {error}")

        with open(PATH_TO_USER_TOKEN, 'w', encoding='utf-8') as user_token_file:
            json.dump(token_for_all_users, user_token_file)
    else:
        print("User token has not exipred yet.")
