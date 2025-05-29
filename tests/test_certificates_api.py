import pytest
from httpx import AsyncClient
from typing import Dict, List, Optional, Any

# Assuming models can be imported for type checks or direct DB verification if needed
# from app.models.certificates import RootCACertificate, CertificateRequest, IssuedCertificate

# --- Fixtures for API tests ---

@pytest.fixture(scope="module")
async def uploaded_root_ca(client: AsyncClient, admin_auth_headers: Dict[str, str]) -> Dict[str, Any]:
    """Fixture to upload a Root CA and make it available for other tests."""
    # Generate a simple self-signed CA for testing purposes
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime

    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test API CA")])
    ca_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)) # Short lived for test
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    )
    ca_cert = ca_builder.sign(ca_key, hashes.SHA256())
    
    ca_cert_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    ca_key_pem = ca_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    payload = {
        "name": "Test API CA",
        "certificate_pem": ca_cert_pem,
        "private_key_pem": ca_key_pem, # Plain text as per current implementation
        "is_issuer": False # Initially not an issuer
    }
    response = await client.post("/certificates/root_ca", json=payload, headers=admin_auth_headers)
    assert response.status_code == 200
    ca_data = response.json()
    
    # Set it as an issuer for subsequent tests
    response_update = await client.put(
        f"/certificates/root_ca/{ca_data['id']}", 
        json={"is_issuer": True}, 
        headers=admin_auth_headers
    )
    assert response_update.status_code == 200
    return response_update.json() # Return the updated CA data which is now an issuer


@pytest.fixture
async def submitted_cert_request(client: AsyncClient, normal_user_auth_headers: Dict[str, str]) -> Dict[str, Any]:
    """Fixture to submit a certificate request as a normal user."""
    payload = {
        "common_name": "user-test.example.com",
        "sans": {"dns": ["user-test.example.com", "alt.user-test.example.com"]}
    }
    response = await client.post("/certificates/requests", json=payload, headers=normal_user_auth_headers)
    assert response.status_code == 200
    return response.json()

# --- Admin API Tests ---
@pytest.mark.asyncio
async def test_admin_upload_root_ca(client: AsyncClient, admin_auth_headers: Dict[str, str]):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime

    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Admin Test CA")])
    ca_builder = (
        x509.CertificateBuilder().subject_name(subject).issuer_name(issuer)
        .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    )
    ca_cert = ca_builder.sign(ca_key, hashes.SHA256())
    ca_cert_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    ca_key_pem = ca_key.private_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    payload = {
        "name": "Admin Test CA Main", "certificate_pem": ca_cert_pem,
        "private_key_pem": ca_key_pem, "is_issuer": True
    }
    response = await client.post("/certificates/root_ca", json=payload, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Admin Test CA Main"
    assert data["is_issuer"] is True
    assert data["encrypted_private_key"] is not None # Check if field is present (plain text key)

@pytest.mark.asyncio
async def test_admin_list_root_cas(client: AsyncClient, admin_auth_headers: Dict[str, str], uploaded_root_ca: Dict[str, Any]):
    response = await client.get("/certificates/root_ca", headers=admin_auth_headers)
    assert response.status_code == 200
    cas = response.json()
    assert isinstance(cas, list)
    assert any(ca['id'] == uploaded_root_ca['id'] for ca in cas)

@pytest.mark.asyncio
async def test_admin_approve_request(
    client: AsyncClient, admin_auth_headers: Dict[str, str], 
    submitted_cert_request: Dict[str, Any], uploaded_root_ca: Dict[str, Any] # Ensure CA is an issuer
):
    request_id = submitted_cert_request["id"]
    response = await client.post(f"/certificates/requests/{request_id}/approve", headers=admin_auth_headers)
    assert response.status_code == 200
    issued_cert_data = response.json()
    assert issued_cert_data["status"] == "valid"
    assert issued_cert_data["request_id"] == request_id
    assert issued_cert_data["issuer_dn"] is not None # Should be populated by CA
    
    # Verify request status updated (optional, could be separate test or DB check)
    # req_response = await client.get(f"/certificates/requests/admin", headers=admin_auth_headers) # Assuming an endpoint to get specific request
    # updated_req = next(r for r in req_response.json() if r['id'] == request_id)
    # assert updated_req['status'] == 'approved'


@pytest.mark.asyncio
async def test_admin_reject_request(client: AsyncClient, admin_auth_headers: Dict[str, str], submitted_cert_request: Dict[str, Any]):
    request_id = submitted_cert_request["id"]
    # Ensure request is pending (if tests run in parallel or fixture re-submits)
    # For this test, we'll assume `submitted_cert_request` provides a fresh, pending request.
    # If not, create a new one for this test.
    
    # If the fixture request might already be approved by another test, create a new one here:
    new_req_payload = {"common_name": "reject-test.example.com", "sans": {"dns": ["reject-test.example.com"]}}
    resp_new_req = await client.post("/certificates/requests", json=new_req_payload, headers=admin_auth_headers) # Submit as admin for simplicity here
    assert resp_new_req.status_code == 200
    request_to_reject_id = resp_new_req.json()["id"]

    rejection_payload = {"status": "rejected", "rejection_reason": "Test rejection"}
    response = await client.post(
        f"/certificates/requests/{request_to_reject_id}/reject", 
        json=rejection_payload, # FastAPI Body() means this should be JSON
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    rejected_req_data = response.json()
    assert rejected_req_data["status"] == "rejected"
    assert rejected_req_data["rejection_reason"] == "Test rejection"

# --- User API Tests ---
@pytest.mark.asyncio
async def test_user_submit_request(client: AsyncClient, normal_user_auth_headers: Dict[str, str]):
    payload = {"common_name": "my.device.com", "sans": {"dns": ["my.device.com"]}}
    response = await client.post("/certificates/requests", json=payload, headers=normal_user_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["common_name"] == "my.device.com"
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_user_list_own_requests(client: AsyncClient, normal_user_auth_headers: Dict[str, str], submitted_cert_request: Dict[str, Any]):
    response = await client.get("/certificates/requests", headers=normal_user_auth_headers)
    assert response.status_code == 200
    requests = response.json()
    assert isinstance(requests, list)
    assert any(req['id'] == submitted_cert_request['id'] for req in requests)
    for req in requests: # Ensure all listed requests belong to the user (conceptual check, relies on API logic)
        assert req['requested_by_id'] == submitted_cert_request['requested_by_id']


@pytest.mark.asyncio
async def test_user_download_own_approved_cert(
    client: AsyncClient, admin_auth_headers: Dict[str, str], 
    normal_user_auth_headers: Dict[str, str], uploaded_root_ca: Dict[str, Any]
):
    # 1. User submits a request
    submit_payload = {"common_name": "download.example.com", "sans": {"dns": ["download.example.com"]}}
    response_submit = await client.post("/certificates/requests", json=submit_payload, headers=normal_user_auth_headers)
    assert response_submit.status_code == 200
    request_data = response_submit.json()
    request_id = request_data["id"]

    # 2. Admin approves it
    response_approve = await client.post(f"/certificates/requests/{request_id}/approve", headers=admin_auth_headers)
    assert response_approve.status_code == 200
    issued_cert_admin_view = response_approve.json()
    issued_certificate_id = issued_cert_admin_view["id"]

    # 3. User downloads it
    response_download = await client.get(
        f"/certificates/issued_certificates/{issued_certificate_id}/download", 
        headers=normal_user_auth_headers
    )
    assert response_download.status_code == 200
    download_data = response_download.json()
    assert "certificate_pem" in download_data
    assert "private_key_pem" in download_data # Will be None if not stored, or plain text if stored
    assert download_data["certificate_pem"].startswith("-----BEGIN CERTIFICATE-----")
    # If private key is stored (as plain text in this phase):
    assert download_data["private_key_pem"] is not None
    assert download_data["private_key_pem"].startswith("-----BEGIN PRIVATE KEY-----")


# --- Permission Tests ---
@pytest.mark.asyncio
async def test_regular_user_cannot_upload_ca(client: AsyncClient, normal_user_auth_headers: Dict[str, str]):
    payload = {"name": "Malicious CA", "certificate_pem": "fake-cert-data", "is_issuer": True}
    response = await client.post("/certificates/root_ca", json=payload, headers=normal_user_auth_headers)
    assert response.status_code == 403 # Or 401 if auth scheme differentiates

@pytest.mark.asyncio
async def test_regular_user_cannot_approve_request(
    client: AsyncClient, normal_user_auth_headers: Dict[str, str], submitted_cert_request: Dict[str, Any]
):
    request_id = submitted_cert_request["id"]
    response = await client.post(f"/certificates/requests/{request_id}/approve", headers=normal_user_auth_headers)
    assert response.status_code == 403 # Or 401

@pytest.mark.asyncio
async def test_user_cannot_download_others_cert(
    client: AsyncClient, admin_auth_headers: Dict[str, str], 
    normal_user_auth_headers: Dict[str, str], # This is User A
    uploaded_root_ca: Dict[str, Any]
):
    # 1. Admin submits a request (or another user B)
    submit_payload_admin = {"common_name": "admin-owned.example.com"}
    response_submit_admin = await client.post("/certificates/requests", json=submit_payload_admin, headers=admin_auth_headers)
    assert response_submit_admin.status_code == 200
    request_data_admin = response_submit_admin.json()
    request_id_admin = request_data_admin["id"]

    # 2. Admin approves it
    response_approve_admin = await client.post(f"/certificates/requests/{request_id_admin}/approve", headers=admin_auth_headers)
    assert response_approve_admin.status_code == 200
    issued_cert_admin_view = response_approve_admin.json()
    issued_certificate_id_admin_owned = issued_cert_admin_view["id"]
    
    # 3. Normal User (User A) tries to download Admin's (User B's) certificate
    response_download_other = await client.get(
        f"/certificates/issued_certificates/{issued_certificate_id_admin_owned}/download", 
        headers=normal_user_auth_headers # User A's token
    )
    assert response_download_other.status_code == 403 # Forbidden

# Note: More tests could be added for edge cases, validation errors, specific contents of certs, etc.
# This suite provides good coverage for core CRUD, user flows, and permissions.
# Database state management between tests (e.g., ensuring a request is 'pending' before testing approval)
# is important. Fixtures help, but for some tests, explicit setup within the test might be needed if
# fixtures are shared and modified by other tests. Ideally, tests should be isolated.
# The `uploaded_root_ca` fixture is set to `is_issuer=True` to allow approvals.
# The `submitted_cert_request` is a basic pending request.
# `admin_auth_headers` and `normal_user_auth_headers` are session-scoped for efficiency.
