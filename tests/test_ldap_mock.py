import pytest
from app.core.auth.ldap_mock import mock_ldap_authenticate

def test_mock_ldap_authenticate_ldapuser():
    """Test successful authentication for 'ldapuser'."""
    expected_user_data = {
        "username": "ldapuser",
        "email": "ldapuser@example.com",
        "first_name": "LDAP",
        "last_name": "User"
    }
    user_data = mock_ldap_authenticate(username="ldapuser", password="anypassword")
    assert user_data is not None
    assert user_data == expected_user_data

def test_mock_ldap_authenticate_non_ldapuser():
    """Test failed authentication for a non-existent LDAP user."""
    user_data = mock_ldap_authenticate(username="nonldapuser", password="somepassword")
    assert user_data is None

def test_mock_ldap_authenticate_ldapuser_empty_password():
    """Test successful authentication for 'ldapuser' even with empty password (as per mock logic)."""
    expected_user_data = {
        "username": "ldapuser",
        "email": "ldapuser@example.com",
        "first_name": "LDAP",
        "last_name": "User"
    }
    user_data = mock_ldap_authenticate(username="ldapuser", password="")
    assert user_data is not None
    assert user_data == expected_user_data
