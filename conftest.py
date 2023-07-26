"""
 Fixtures and Hooks Configuraiton
 """
import asyncio
from setUp import set_admin_and_user_token as setToken


def pytest_sessionstart():
    """
    Get Set Admin and User Token
    """
    async def setup_token():
        await setToken.set_up_admin_token()
        await setToken.set_up_user_token()

    asyncio.run(setup_token())
