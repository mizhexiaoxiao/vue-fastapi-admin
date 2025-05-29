import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta, timezone
import os

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, AuthorityInformationAccessOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12

# Adjust import path based on how tests will be run.
# Assuming PYTHONPATH is set to project root (e.g., `PYTHONPATH=. python -m unittest ...`)
from app.core import certs as core_certs
from app.settings import config as app_config # For mocking settings

# Helper function to generate a dummy RSA key for testing
def generate_test_rsa_key(key_size=2048):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return private_key

def generate_pem_public_key(private_key):
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

def generate_pem_private_key(private_key, encryption_algorithm=None, password=None):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm if encryption_algorithm else serialization.NoEncryption()
    ).decode('utf-8')

def generate_self_signed_ca_cert(common_name, private_key, days_valid=365):
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days_valid))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(key_cert_sign=True, crl_sign=True, digital_signature=False, content_commitment=False, key_encipherment=False, data_encipherment=False, key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
    )
    certificate = builder.sign(private_key, hashes.SHA256())
    return certificate

class TestLoadCAResources(unittest.TestCase):

    def setUp(self):
        self.ca_key = generate_test_rsa_key()
        self.ca_cert = generate_self_signed_ca_cert("Test CA", self.ca_key)
        self.ca_cert_pem = self.ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        self.ca_key_pem_unencrypted = generate_pem_private_key(self.ca_key)
        self.ca_key_pem_encrypted = generate_pem_private_key(
            self.ca_key, 
            serialization.BestAvailableEncryption(b"testpassword"),
            b"testpassword" # this argument is for the key itself, not for the encryption_algorithm
        )

    @patch('app.core.certs.settings')
    @patch('builtins.open', new_callable=mock_open)
    def test_success_unencrypted_key(self, mock_file, mock_settings):
        mock_settings.CA_CERT_PATH = "dummy_ca_cert.pem"
        mock_settings.CA_PRIVATE_KEY_PATH = "dummy_ca_key.pem"
        mock_settings.CA_PRIVATE_KEY_PASSWORD = None
        
        mock_file.side_effect = [
            mock_open(read_data=self.ca_cert_pem.encode()).return_value,  # For CA cert
            mock_open(read_data=self.ca_key_pem_unencrypted.encode()).return_value  # For CA key
        ]
        
        loaded_cert, loaded_key = core_certs.load_ca_resources()
        self.assertIsNotNone(loaded_cert)
        self.assertIsNotNone(loaded_key)
        self.assertEqual(loaded_cert.serial_number, self.ca_cert.serial_number)

    @patch('app.core.certs.settings')
    @patch('builtins.open', new_callable=mock_open)
    def test_success_encrypted_key(self, mock_file, mock_settings):
        mock_settings.CA_CERT_PATH = "dummy_ca_cert.pem"
        mock_settings.CA_PRIVATE_KEY_PATH = "dummy_ca_key_enc.pem"
        mock_settings.CA_PRIVATE_KEY_PASSWORD = "testpassword"

        mock_file.side_effect = [
            mock_open(read_data=self.ca_cert_pem.encode()).return_value,
            mock_open(read_data=self.ca_key_pem_encrypted.encode()).return_value
        ]

        loaded_cert, loaded_key = core_certs.load_ca_resources()
        self.assertIsNotNone(loaded_cert)
        self.assertIsNotNone(loaded_key)
        # Simple check, details depend on how key objects are compared
        self.assertTrue(isinstance(loaded_key, rsa.RSAPrivateKey))

    @patch('app.core.certs.settings')
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_cert_file_not_found(self, mock_file_open, mock_settings):
        mock_settings.CA_CERT_PATH = "non_existent_cert.pem"
        mock_settings.CA_PRIVATE_KEY_PATH = "dummy_ca_key.pem"
        mock_settings.CA_PRIVATE_KEY_PASSWORD = None
        
        loaded_cert, loaded_key = core_certs.load_ca_resources()
        self.assertIsNone(loaded_cert)
        self.assertIsNone(loaded_key)

    @patch('app.core.certs.settings')
    @patch('builtins.open', new_callable=mock_open)
    def test_invalid_key_pem(self, mock_file, mock_settings):
        mock_settings.CA_CERT_PATH = "dummy_ca_cert.pem"
        mock_settings.CA_PRIVATE_KEY_PATH = "invalid_key.pem"
        mock_settings.CA_PRIVATE_KEY_PASSWORD = None

        mock_file.side_effect = [
            mock_open(read_data=self.ca_cert_pem.encode()).return_value,
            mock_open(read_data=b"-----BEGIN PRIVATE KEY-----\ninvalid data\n-----END PRIVATE KEY-----").return_value
        ]
        loaded_cert, loaded_key = core_certs.load_ca_resources()
        self.assertIsNone(loaded_key) # Cert might load, but key should fail
        # self.assertIsNone(loaded_cert) # Depending on desired behavior if key fails

    @patch('app.core.certs.settings')
    @patch('builtins.open', new_callable=mock_open)
    def test_incorrect_key_password(self, mock_file, mock_settings):
        mock_settings.CA_CERT_PATH = "dummy_ca_cert.pem"
        mock_settings.CA_PRIVATE_KEY_PATH = "dummy_ca_key_enc.pem"
        mock_settings.CA_PRIVATE_KEY_PASSWORD = "wrongpassword"

        mock_file.side_effect = [
            mock_open(read_data=self.ca_cert_pem.encode()).return_value,
            mock_open(read_data=self.ca_key_pem_encrypted.encode()).return_value
        ]
        loaded_cert, loaded_key = core_certs.load_ca_resources()
        self.assertIsNone(loaded_key) # Key should fail to load


class TestGenerateX509Certificate(unittest.TestCase):

    def setUp(self):
        self.ca_key = generate_test_rsa_key()
        self.ca_cert = generate_self_signed_ca_cert("Test CA", self.ca_key)
        self.user_key = generate_test_rsa_key()
        self.user_public_key_pem = generate_pem_public_key(self.user_key)

    @patch('app.core.certs.load_ca_resources')
    def test_success_basic_generation(self, mock_load_ca):
        mock_load_ca.return_value = (self.ca_cert, self.ca_key)
        
        cn = "test.example.com"
        sans = ["dns:test.example.com", "ip:192.168.1.1"]
        ekus = [ExtendedKeyUsageOID.SERVER_AUTH.dotted_string, ExtendedKeyUsageOID.CLIENT_AUTH.dotted_string]
        days = 30

        cert_pem = core_certs.generate_x509_certificate(
            user_common_name=cn,
            subject_alt_names_data=sans,
            ekus_data=ekus,
            requested_days=days,
            public_key_pem=self.user_public_key_pem
        )
        self.assertIsNotNone(cert_pem)
        self.assertTrue(cert_pem.startswith("-----BEGIN CERTIFICATE-----"))

        # Inspect generated certificate
        gen_cert = x509.load_pem_x509_certificate(cert_pem.encode(), None)
        self.assertEqual(gen_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value, cn)
        self.assertEqual(gen_cert.issuer, self.ca_cert.subject) # Should be issued by our mock CA
        
        # Validity (approximate check for days)
        expected_expiry_delta = timedelta(days=days)
        self.assertAlmostEqual(gen_cert.not_valid_after_utc - gen_cert.not_valid_before_utc, expected_expiry_delta, delta=timedelta(seconds=10))

        # SANs
        san_ext = gen_cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        self.assertIsNotNone(san_ext)
        dns_names = san_ext.value.get_values_for_type(x509.DNSName)
        ip_addrs = san_ext.value.get_values_for_type(x509.IPAddress)
        self.assertIn("test.example.com", dns_names)
        self.assertIn(ipaddress.ip_address("192.168.1.1"), ip_addrs)

        # EKUs
        eku_ext = gen_cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
        self.assertIsNotNone(eku_ext)
        self.assertIn(ExtendedKeyUsageOID.SERVER_AUTH, eku_ext.value)
        self.assertIn(ExtendedKeyUsageOID.CLIENT_AUTH, eku_ext.value)

        # Basic Constraints
        bc_ext = gen_cert.extensions.get_extension_for_class(x509.BasicConstraints)
        self.assertIsNotNone(bc_ext)
        self.assertFalse(bc_ext.value.ca)

        # Key Usage
        ku_ext = gen_cert.extensions.get_extension_for_class(x509.KeyUsage)
        self.assertTrue(ku_ext.value.digital_signature)
        self.assertTrue(ku_ext.value.key_encipherment)


    @patch('app.core.certs.load_ca_resources')
    def test_load_ca_failure(self, mock_load_ca):
        mock_load_ca.return_value = (None, None)
        cert_pem = core_certs.generate_x509_certificate("test", [], [], 30, self.user_public_key_pem)
        self.assertIsNone(cert_pem)

    def test_invalid_public_key_pem(self):
        cert_pem = core_certs.generate_x509_certificate("test", [], [], 30, "invalid pem")
        self.assertIsNone(cert_pem)


class TestConvertPemToPfx(unittest.TestCase):
    def setUp(self):
        self.user_key = generate_test_rsa_key()
        self.user_cert = generate_self_signed_ca_cert("user.example.com", self.user_key, days_valid=30) # Self-signed for simplicity
        self.user_cert_pem = self.user_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        self.user_key_pem = generate_pem_private_key(self.user_key)

        # Create a dummy CA for chain testing
        self.ca_key = generate_test_rsa_key()
        self.ca_cert = generate_self_signed_ca_cert("Test CA", self.ca_key, days_valid=365)
        self.ca_cert_pem = self.ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')

        self.cert_chain_pem = self.user_cert_pem + "\n" + self.ca_cert_pem

    def test_success_with_password(self):
        pfx_data = core_certs.convert_pem_to_pfx(
            user_pem_cert_chain_str=self.cert_chain_pem,
            user_private_key_pem_str=self.user_key_pem,
            pfx_password="testpfxpassword"
        )
        self.assertIsNotNone(pfx_data)
        self.assertIsInstance(pfx_data, bytes)

        # Optional: verify by parsing
        key, cert, cas = pkcs12.load_key_and_certificates(pfx_data, b"testpfxpassword")
        self.assertIsNotNone(key)
        self.assertIsNotNone(cert)
        self.assertEqual(cert.serial_number, self.user_cert.serial_number)
        self.assertEqual(len(cas), 1)
        self.assertEqual(cas[0].serial_number, self.ca_cert.serial_number)


    def test_success_without_password(self):
        pfx_data = core_certs.convert_pem_to_pfx(
            user_pem_cert_chain_str=self.user_cert_pem, # Just user cert for this test
            user_private_key_pem_str=self.user_key_pem,
            pfx_password=None 
        )
        self.assertIsNotNone(pfx_data)
        self.assertIsInstance(pfx_data, bytes)
        
        # Optional: verify by parsing (no password)
        key, cert, cas = pkcs12.load_key_and_certificates(pfx_data, None)
        self.assertIsNotNone(key)
        self.assertIsNotNone(cert)
        self.assertEqual(cert.serial_number, self.user_cert.serial_number)
        self.assertIsNone(cas) # Only user cert was bundled

    def test_invalid_pem_cert_input(self):
        pfx_data = core_certs.convert_pem_to_pfx(
            user_pem_cert_chain_str="invalid cert pem",
            user_private_key_pem_str=self.user_key_pem,
            pfx_password="test"
        )
        self.assertIsNone(pfx_data)

    def test_invalid_pem_key_input(self):
        pfx_data = core_certs.convert_pem_to_pfx(
            user_pem_cert_chain_str=self.user_cert_pem,
            user_private_key_pem_str="invalid key pem",
            pfx_password="test"
        )
        self.assertIsNone(pfx_data)

if __name__ == '__main__':
    # This allows running the tests directly.
    # For integration with a test runner, this part might not be necessary,
    # and PYTHONPATH adjustments might be handled by the runner's config.
    
    # If app module is not found, try adding project root to PYTHONPATH
    # This is a common pattern if tests are in a subfolder.
    # import sys
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.abspath(os.path.join(current_dir, "..", "..")) 
    # if project_root not in sys.path:
    #    sys.path.insert(0, project_root)
    
    # from app.core import certs as core_certs # Re-import if path was adjusted
    # from app.settings import config as app_config

    unittest.main()
