from setUp import set_admin_and_user_token as setToken
import asyncio


# @pytest.fixture(scope='session', autouse=True)
def pytest_sessionstart(session):
    async def setup_token():
        await setToken.set_up_admin_token()
        await setToken.set_up_user_token()

    asyncio.run(setup_token())
