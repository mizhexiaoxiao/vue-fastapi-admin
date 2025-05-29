import unittest
from unittest.mock import patch, AsyncMock, MagicMock # AsyncMock for Tortoise methods
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Patch init_data BEFORE importing app from run
# This is crucial to prevent database connections during test setup.
# We assume init_data is a function that can be patched.
# If it's more complex, this might need adjustment.
mock_init_data = MagicMock()
patch_init_data = patch('run.init_data', mock_init_data)
patch_init_data.start()

# Now import the app
from run import app # Assuming run.py is in the root and importable

# Stop the patch after app is imported if it's no longer needed for other test modules
# or manage its lifecycle within test classes/methods if more fine-grained control is needed.
# For now, we'll leave it patched for the duration of this test module.
# patch_init_data.stop() # If we were to stop it.

from app.core.dependency import get_current_active_user, get_current_super_user
from app.models.admin import User as UserModel
from app.schemas.certificate import (
    CertificateRequestCreate, 
    CertificateRequestRead, 
    CertificateRequestAdminUpdate,
    RequestStatusEnum,
    IssuedCertificateDetails, # Though this is part of response, good to have for structure check
    CertificateActionResponse
)
# For mocking generate_x509_certificate and parsing its output
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from datetime import timedelta


# Helper to generate a dummy certificate for mocking generate_x509_certificate
def generate_dummy_pem_cert(cn="test.example.com", days=30, serial=12345):
    key = rsa.generate_private_key(public_exponent=65537, key_size=512) # Small key for speed
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(serial)
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    )
    certificate = builder.sign(key, hashes.SHA256())
    return certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8'), certificate


class TestCertificateRequestsAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mock_active_user = UserModel(id=1, username="testuser", email="test@example.com", is_active=True, is_superuser=False)
        cls.mock_super_user = UserModel(id=2, username="adminuser", email="admin@example.com", is_active=True, is_superuser=True)

        def override_get_current_active_user():
            return cls.mock_active_user

        def override_get_current_super_user():
            return cls.mock_super_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user
        app.dependency_overrides[get_current_super_user] = override_get_current_super_user
        
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides = {} # Clean up overrides
        patch_init_data.stop() # Stop the init_data patch

    @patch('app.models.certificate.CertificateRequest.create', new_callable=AsyncMock)
    async def test_submit_certificate_request_success(self, mock_request_create):
        # Prepare mock return value for CertificateRequest.create
        # It should return an object that can be serialized by CertificateRequestRead.from_tortoise_orm
        mock_created_request_obj = MagicMock()
        mock_created_request_obj.id = 1
        mock_created_request_obj.user_id = self.mock_active_user.id
        mock_created_request_obj.common_name = "test.example.com"
        mock_created_request_obj.distinguished_name_json = {"CN": "test.example.com"}
        mock_created_request_obj.sans = ["dns:test.example.com"]
        mock_created_request_obj.ekus = []
        mock_created_request_obj.requested_days = 30
        mock_created_request_obj.public_key_pem = "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
        mock_created_request_obj.status = RequestStatusEnum.PENDING.value
        mock_created_request_obj.rejection_reason = None
        mock_created_request_obj.approved_at = None
        mock_created_request_obj.created_at = datetime.now(timezone.utc)
        mock_created_request_obj.updated_at = datetime.now(timezone.utc)
        
        mock_request_create.return_value = mock_created_request_obj

        # Patch from_tortoise_orm to return a dictionary directly for easier assertion
        # or ensure your mock_created_request_obj is compatible
        with patch('app.schemas.certificate.CertificateRequestRead.from_tortoise_orm', AsyncMock(return_value=CertificateRequestRead.model_validate(mock_created_request_obj.__dict__))):
            request_payload = {
                "common_name": "test.example.com",
                "distinguished_name_json": {"CN": "test.example.com"},
                "sans": ["dns:test.example.com"],
                "ekus": [],
                "requested_days": 30,
                "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
            }
            response = self.client.post("/api/v1/certificate-requests/", json=request_payload)

        self.assertEqual(response.status_code, 201)
        json_response = response.json()
        self.assertEqual(json_response["common_name"], request_payload["common_name"])
        self.assertEqual(json_response["status"], RequestStatusEnum.PENDING.value)
        
        mock_request_create.assert_awaited_once()
        # Further assertions can be made on the arguments passed to mock_request_create


    def test_submit_request_invalid_data(self):
        request_payload = { # Missing common_name and public_key_pem
            "requested_days": 30
        }
        response = self.client.post("/api/v1/certificate-requests/", json=request_payload)
        self.assertEqual(response.status_code, 422) # Unprocessable Entity for Pydantic validation errors


    @patch('app.models.certificate.IssuedCertificate.create', new_callable=AsyncMock)
    @patch('app.core.certs.generate_x509_certificate')
    @patch('app.models.certificate.CertificateRequest.get_or_none', new_callable=AsyncMock)
    async def test_admin_approve_request_success(self, mock_get_request, mock_generate_cert, mock_create_issued_cert):
        request_id = 1
        mock_request_obj = MagicMock(spec=['id', 'user_id', 'common_name', 'sans', 'ekus', 'requested_days', 'public_key_pem', 'status', 'save'])
        mock_request_obj.id = request_id
        mock_request_obj.user_id = self.mock_active_user.id
        mock_request_obj.common_name = "approved.example.com"
        mock_request_obj.sans = ["dns:approved.example.com"]
        mock_request_obj.ekus = []
        mock_request_obj.requested_days = 90
        mock_request_obj.public_key_pem = "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
        mock_request_obj.status = RequestStatusEnum.PENDING.value
        mock_request_obj.save = AsyncMock() # Make save awaitable
        mock_get_request.return_value = mock_request_obj

        dummy_pem, dummy_cert_obj = generate_dummy_pem_cert(cn=mock_request_obj.common_name, days=mock_request_obj.requested_days, serial=5678)
        mock_generate_cert.return_value = dummy_pem
        
        mock_create_issued_cert.return_value = MagicMock() # Simulate successful creation

        # Patch from_tortoise_orm for CertificateRequestRead
        with patch('app.schemas.certificate.CertificateRequestRead.from_tortoise_orm', AsyncMock(return_value=CertificateRequestRead.model_validate(mock_request_obj.__dict__))):
            action_payload = {"status": RequestStatusEnum.APPROVED.value}
            response = self.client.post(f"/api/v1/certificate-requests/admin/{request_id}/action", json=action_payload)
        
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertEqual(json_response["request_status"]["status"], RequestStatusEnum.ISSUED.value)
        self.assertIsNotNone(json_response["issued_certificate_details"])
        self.assertEqual(json_response["issued_certificate_details"]["certificate_pem"], dummy_pem)

        mock_generate_cert.assert_called_once_with(
            user_common_name=mock_request_obj.common_name,
            subject_alt_names_data=mock_request_obj.sans,
            ekus_data=mock_request_obj.ekus,
            requested_days=mock_request_obj.requested_days,
            public_key_pem=mock_request_obj.public_key_pem
        )
        mock_create_issued_cert.assert_awaited_once()
        # Assert serial and expiry match dummy_cert_obj
        args, _ = mock_create_issued_cert.call_args
        self.assertEqual(args[0]['serial_number'], str(dummy_cert_obj.serial_number))
        self.assertEqual(args[0]['expires_at'], dummy_cert_obj.not_valid_after_utc)
        
        mock_request_obj.save.assert_awaited_once()
        self.assertEqual(mock_request_obj.status, RequestStatusEnum.ISSUED.value)


    @patch('app.core.certs.generate_x509_certificate')
    @patch('app.models.certificate.CertificateRequest.get_or_none', new_callable=AsyncMock)
    async def test_admin_approve_generation_failure(self, mock_get_request, mock_generate_cert):
        request_id = 2
        mock_request_obj = MagicMock(spec=['id', 'status', 'save', 'common_name', 'sans', 'ekus', 'requested_days', 'public_key_pem'])
        mock_request_obj.id = request_id
        mock_request_obj.status = RequestStatusEnum.PENDING.value
        mock_request_obj.save = AsyncMock()
        mock_request_obj.common_name = "fail.example.com" # Add other necessary attributes for generate_x509_certificate call
        mock_request_obj.sans = []
        mock_request_obj.ekus = []
        mock_request_obj.requested_days = 30
        mock_request_obj.public_key_pem = "key"
        mock_get_request.return_value = mock_request_obj

        mock_generate_cert.return_value = None # Simulate generation failure

        action_payload = {"status": RequestStatusEnum.APPROVED.value}
        response = self.client.post(f"/api/v1/certificate-requests/admin/{request_id}/action", json=action_payload)
        
        self.assertEqual(response.status_code, 500) # As per endpoint logic
        mock_request_obj.save.assert_awaited_once()
        self.assertEqual(mock_request_obj.status, RequestStatusEnum.FAILED.value)


    @patch('app.models.certificate.CertificateRequest.get_or_none', new_callable=AsyncMock)
    async def test_admin_reject_request_success(self, mock_get_request):
        request_id = 3
        mock_request_obj = MagicMock(spec=['id', 'status', 'save', 'rejection_reason', 'approved_at'])
        mock_request_obj.id = request_id
        mock_request_obj.status = RequestStatusEnum.PENDING.value
        mock_request_obj.save = AsyncMock()
        mock_get_request.return_value = mock_request_obj

        rejection_reason = "Policy violation"
        action_payload = {"status": RequestStatusEnum.REJECTED.value, "rejection_reason": rejection_reason}
        
        with patch('app.schemas.certificate.CertificateRequestRead.from_tortoise_orm', AsyncMock(return_value=CertificateRequestRead.model_validate(mock_request_obj.__dict__))):
            response = self.client.post(f"/api/v1/certificate-requests/admin/{request_id}/action", json=action_payload)

        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertEqual(json_response["request_status"]["status"], RequestStatusEnum.REJECTED.value)
        
        mock_request_obj.save.assert_awaited_once()
        self.assertEqual(mock_request_obj.status, RequestStatusEnum.REJECTED.value)
        self.assertEqual(mock_request_obj.rejection_reason, rejection_reason)

    @patch('app.models.certificate.CertificateRequest.get_or_none', new_callable=AsyncMock)
    async def test_admin_request_not_found(self, mock_get_request):
        mock_get_request.return_value = None
        action_payload = {"status": RequestStatusEnum.APPROVED.value}
        response = self.client.post("/api/v1/certificate-requests/admin/999/action", json=action_payload)
        self.assertEqual(response.status_code, 404)

# To run these tests (assuming this file is tests/api/test_certificate_requests_api.py):
# Ensure run.py and app/ are in PYTHONPATH. From project root:
# PYTHONPATH=. python -m unittest tests.api.test_certificate_requests_api
# Note: AsyncMock requires Python 3.8+. If using older, regular MagicMock with awaitable side_effects might be needed.
# The environment for this task is Python 3.11, so AsyncMock is fine.

if __name__ == '__main__':
    # This setup is a bit more involved if run directly due to async nature and FastAPI TestClient
    # Typically, a test runner like pytest with pytest-asyncio would handle the event loop.
    # For unittest, if you need to run async test methods directly, you might wrap them.
    # However, TestClient typically handles the async event loop for you.
    
    # If running this file directly, you might need to adjust sys.path for imports:
    # import sys, os
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.abspath(os.path.join(current_dir, "..", "..")) 
    # if project_root not in sys.path:
    #    sys.path.insert(0, project_root)

    unittest.main()
