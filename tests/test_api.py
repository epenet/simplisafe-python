"""Define tests for the System object."""
# pylint: disable=protected-access,too-many-arguments
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from simplipy import API
from simplipy.errors import InvalidCredentialsError, RequestError, SimplipyError

from .common import (
    TEST_ACCESS_TOKEN,
    TEST_AUTHORIZATION_CODE,
    TEST_CODE_VERIFIER,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
)


@pytest.mark.asyncio
async def test_401_bad_credentials(aresponses, invalid_authorization_code_response):
    """Test that an InvalidCredentialsError is raised with an invalid auth code."""
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(
            invalid_authorization_code_response, status=401
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_401_refresh_token_failure(
    aresponses, invalid_refresh_token_response, server
):
    """Test that an error is raised when refresh token and reauth both fail."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(
            invalid_refresh_token_response, status=403
        ),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        # Manually set the expiration datetime to force a refresh token flow:
        simplisafe._token_last_refreshed = datetime.utcnow() - timedelta(seconds=30)

        with pytest.raises(InvalidCredentialsError):
            await simplisafe.async_get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_401_refresh_token_success(
    api_token_response,
    aresponses,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that a successful refresh token carries out the original request."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )

    api_token_response["access_token"] = "jjhhgg66"
    api_token_response["refresh_token"] = "aabbcc11"

    server.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(
            v2_subscriptions_response, status=200
        ),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aiohttp.web_response.json_response(v2_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        # Manually set the expiration datetime to force a refresh token flow:
        simplisafe._token_last_refreshed = datetime.utcnow() - timedelta(seconds=30)

        # If this succeeds without throwing an exception, the retry is successful:
        await simplisafe.async_get_systems()
        assert simplisafe.access_token == "jjhhgg66"
        assert simplisafe.refresh_token == "aabbcc11"

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_403_bad_credentials(aresponses, invalid_authorization_code_response):
    """Test that an InvalidCredentialsError is raised with a 403."""
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(
            invalid_authorization_code_response, status=403
        ),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )


@pytest.mark.asyncio
async def test_client_async_from_authorization_code(
    api_token_response, aresponses, auth_check_response
):
    """Test creating a client from an authorization code."""
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        response=aiohttp.web_response.json_response(auth_check_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        assert simplisafe.access_token == TEST_ACCESS_TOKEN
        assert simplisafe.refresh_token == TEST_REFRESH_TOKEN

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_client_async_from_authorization_code_unknown_error():
    """Test an unknown error while creating a client from an authorization code."""
    with patch("simplipy.API._async_request", AsyncMock(side_effect=Exception)):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(SimplipyError):
                await API.async_from_auth(
                    TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
                )


@pytest.mark.asyncio
async def test_client_async_from_refresh_token(
    api_token_response, aresponses, auth_check_response
):
    """Test creating a client from a refresh token."""
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        response=aiohttp.web_response.json_response(auth_check_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_refresh_token(
            TEST_REFRESH_TOKEN, session=session
        )
        assert simplisafe.access_token == TEST_ACCESS_TOKEN
        assert simplisafe.refresh_token == TEST_REFRESH_TOKEN

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_client_async_from_refresh_token_unknown_error():
    """Test an unknown error while creating a client from a refresh token."""
    with patch("simplipy.API._async_request", AsyncMock(side_effect=Exception)):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(SimplipyError):
                await API.async_from_refresh_token(TEST_REFRESH_TOKEN, session=session)


@pytest.mark.asyncio
async def test_refresh_token_callback(
    api_token_response,
    aresponses,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that callbacks are executed correctly."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aresponses.Response(text="Unauthorized", status=401),
    )

    api_token_response["access_token"] = "jjhhgg66"
    api_token_response["refresh_token"] = "aabbcc11"

    server.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(
            v2_subscriptions_response, status=200
        ),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aiohttp.web_response.json_response(v2_settings_response, status=200),
    )

    mock_callback_1 = Mock()
    mock_callback_2 = Mock()

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        # Manually set the expiration datetime to force a refresh token flow:
        simplisafe._token_last_refreshed = datetime.utcnow() - timedelta(seconds=30)

        # We'll hang onto one callback:
        simplisafe.add_refresh_token_callback(mock_callback_1)
        assert mock_callback_1.call_count == 0

        # ..and delete the a second one before ever using it:
        remove = simplisafe.add_refresh_token_callback(mock_callback_2)
        remove()

        await simplisafe.async_get_systems()
        await asyncio.sleep(1)
        mock_callback_1.assert_called_once_with("aabbcc11")
        assert mock_callback_1.call_count == 1
        assert mock_callback_2.call_count == 0


@pytest.mark.asyncio
async def test_request_retry(
    api_token_response,
    aresponses,
    server,
    v2_settings_response,
    v2_subscriptions_response,
):
    """Test that request retries work."""
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Conflict", status=409),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aresponses.Response(text="Conflict", status=409),
    )
    server.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web_response.json_response(api_token_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(
            v2_subscriptions_response, status=200
        ),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aiohttp.web_response.json_response(v2_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        simplisafe.disable_request_retries()

        with pytest.raises(RequestError):
            await simplisafe.async_get_systems()

        simplisafe.enable_request_retries()

        # If this succeeds without throwing an exception, the retry is successful:
        await simplisafe.async_get_systems()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_string_response(aresponses):
    """Test that a quoted stringn response is handled correctly."""
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aresponses.Response(text='"Unauthorized"', status=401),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidCredentialsError):
            await API.async_from_auth(
                TEST_AUTHORIZATION_CODE,
                TEST_CODE_VERIFIER,
                session=session,
                # Set so that our tests don't take too long:
                request_retries=1,
            )

    aresponses.assert_plan_strictly_followed()
