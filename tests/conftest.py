import pytest
import asyncio
from httpx import AsyncClient
from typing import AsyncGenerator, Dict, Any

# Import your FastAPI app instance
# This might be `from app.main import app` or wherever your app is defined
# For this example, let's assume it's `from app.main import app`
# If app.main doesn't exist or is not the entry point, this needs adjustment.
# It also implies that running pytest needs PYTHONPATH to include the app's root.
try:
    from app.main import app # Assuming your FastAPI app instance is here
except ImportError:
    # Fallback for environments where app.main might not be the typical entry
    # This part is highly dependent on project structure.
    # A common pattern is to have a create_app() function.
    from fastapi import FastAPI
    from app.api import api_router
    from app.core.init_app import register_routers, register_exceptions, make_middlewares, init_data

    def create_test_app() -> FastAPI:
        test_app = FastAPI(
            title="Test App",
            middleware=make_middlewares(),
        )
        register_routers(test_app, prefix="/api")
        register_exceptions(test_app)

        @test_app.on_event("startup")
        async def startup_event():
            # This would ideally set up a test database
            # For now, we assume init_data can run if needed, or DB is pre-configured
            print("Test app startup: Initializing data (if configured for test env)...")
            # await init_data() # Be cautious with this in tests; it might run full DB init
            pass

        return test_app
    app = create_test_app()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://testserver/api/v1") as ac:
        # Wait for startup event if your app has one that needs to complete
        # This might involve a more sophisticated wait if startup tasks are long
        await asyncio.sleep(0.1) # Small delay for startup events
        yield ac

@pytest.fixture(scope="session")
async def admin_auth_headers(client: AsyncClient) -> Dict[str, str]:
    response = await client.post("/base/access_token", data={"username": "admin", "password": "123456"})
    if response.status_code != 200:
        raise Exception(f"Failed to authenticate admin: {response.text}")
    tokens = response.json()["data"]
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@pytest.fixture(scope="session")
async def normal_user_auth_headers(client: AsyncClient) -> Dict[str, str]:
    # This assumes 'ldapuser' can log in and gets the "普通用户" role.
    # The mock LDAP auth allows any password for 'ldapuser'.
    response = await client.post("/base/access_token", data={"username": "ldapuser", "password": "testpassword"})
    if response.status_code != 200:
        # This might fail if init_data() wasn't fully run to create roles, or if ldapuser isn't assigned a role upon creation
        # For robustness, could pre-create ldapuser and assign role if test setup allows
        raise Exception(f"Failed to authenticate normal_user (ldapuser): {response.text}. Ensure init_data created roles and LDAP user gets a role.")
    tokens = response.json()["data"]
    return {"Authorization": f"Bearer {tokens['access_token']}"}

# Fixture to ensure init_data runs once per session if needed for DB setup
# This is a simplified version; real test DB management is more complex.
_data_initialized = False

@pytest.fixture(scope="session", autouse=True)
async def initialize_data_once():
    global _data_initialized
    if not _data_initialized:
        # This is tricky because init_data also initializes Tortoise ORM
        # which might conflict if Tortoise is already initialized by FastAPI app startup.
        # For a robust solution, use a dedicated test DB and manage schema with Aerich.
        # For now, we assume the app startup handles DB init or it's done externally.
        # If your app relies on init_data() for roles/users, it must be run carefully.
        # await init_data() # Potentially problematic, see notes
        print("Skipping automatic init_data() in conftest. Assume DB is set up or app startup handles it.")
        _data_initialized = True
        # It's better to ensure your test environment (e.g., Docker Compose for tests)
        # starts with a database that has had init_data() run against it.
        # Or, use transaction-based tests that roll back, but that's complex with async.

        # A common pattern for Tortoise ORM in tests:
        # from tortoise.contrib.test import finalizer, initializer
        # initializer(["app.models"]) # List your model modules
        # request.addfinalizer(finalizer)
        # This would be per-test or per-module, not session scope for isolation.
        pass
