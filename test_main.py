import json
import argparse
from dotenv import load_dotenv
import os
import httpx
import pytest
from setUp import set_admin_and_user_token as setToken

# variables:

program_uuid = "de5e58b5-1fce-4eba-a7c2-7ae4e47e48bd"


parser = argparse.ArgumentParser()
parser.add_argument("--env_file", default="staging",
                    help="Please Specify .env file name")
args = parser.parse_args()

env_path = f"env/.env.{args.env_file}"

load_dotenv(env_path)

password = os.getenv("USER_PASSWORD")


@pytest.mark.asyncio
async def test_answer():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/todos/1")
        assert response.status_code == 200


def test_verifyPassword():
    assert password == "password123"


async def apply(user_access_token: str, programUuid: str):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {user_access_token}'
    }
    payload = {
        "offeringUuid": programUuid
    }
    apply_url = os.getenv("APPLY")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url=apply_url, headers=headers, json=payload)
            json_data_from_response = response.json()
            return json_data_from_response
    except Exception as e:
        print(f"Error occured on /apply route: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("property_name", [
    'id',
    'user_id',
    'progress',
    'state',
    'language',
    'program_uuid',
    'data',
])
async def test_apply_route_properties(property_name):
    with open(setToken.path_to_user_token, 'r', encoding='utf-8') as file:
        file_data = file.read()
        user_token_data = json.loads(file_data)

    email_access_token_map = {}
    for user_token in user_token_data:
        email = list(user_token.keys())[0]
        access_token = user_token[email]['access_token']
        email_access_token_map[email] = access_token

    for each_email in setToken.user_email_list:
        json_data_from_apply_route = await apply(user_access_token=email_access_token_map[each_email], programUuid=program_uuid)
        assert property_name in json_data_from_apply_route
