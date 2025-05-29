import pytest
import datetime
import ipaddress
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

from app.core.certificate_utils import (
    load_ca_private_key,
    load_ca_certificate,
    generate_signed_certificate,
    RootCACertificate as PlaceholderRootCA, # Use placeholder if direct import is an issue
    CertificateRequest as PlaceholderCertRequest
)
from app.settings.config import settings # For CRL_DISTRIBUTION_POINT_URL

# --- Mock Data and Fixtures ---

@pytest.fixture(scope="module")
def mock_ca_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)

@pytest.fixture(scope="module")
def mock_ca_cert(mock_ca_key: rsa.RSAPrivateKey) -> x509.Certificate:
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(mock_ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365 * 5))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(mock_ca_key.public_key()), critical=False)
    )
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(mock_ca_key.public_key()), critical=False
    )
    certificate = builder.sign(mock_ca_key, hashes.SHA256())
    return certificate

@pytest.fixture
def mock_root_ca_model(mock_ca_cert: x509.Certificate, mock_ca_key: rsa.RSAPrivateKey) -> PlaceholderRootCA:
    ca = PlaceholderRootCA()
    ca.certificate_pem = mock_ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    # Simulating plain text storage for the test, as per current util logic
    ca.encrypted_private_key = mock_ca_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    ca.private_key_salt = None # Not used in plain text scenario
    ca.is_issuer = True
    ca.name = "Test CA"
    return ca

@pytest.fixture
def mock_cert_request_data() -> PlaceholderCertRequest:
    req = PlaceholderCertRequest()
    req.common_name = "test.example.com"
    req.sans = {
        "dns": ["test.example.com", "www.test.example.com"],
        "ip": ["192.0.2.1", "2001:db8::1"]
    }
    return req

# --- Tests for load_ca_private_key ---

def test_load_ca_private_key_valid(mock_root_ca_model: PlaceholderRootCA):
    key = load_ca_private_key(mock_root_ca_model)
    assert isinstance(key, rsa.RSAPrivateKey)

def test_load_ca_private_key_missing(mock_root_ca_model: PlaceholderRootCA):
    mock_root_ca_model.encrypted_private_key = None
    with pytest.raises(ValueError, match="CA private key is missing"):
        load_ca_private_key(mock_root_ca_model)

def test_load_ca_private_key_invalid_pem(mock_root_ca_model: PlaceholderRootCA):
    mock_root_ca_model.encrypted_private_key = "INVALID KEY DATA"
    with pytest.raises(ValueError, match="Failed to load CA private key"):
        load_ca_private_key(mock_root_ca_model)

# --- Tests for load_ca_certificate ---

def test_load_ca_certificate_valid(mock_root_ca_model: PlaceholderRootCA):
    cert = load_ca_certificate(mock_root_ca_model)
    assert isinstance(cert, x509.Certificate)
    assert cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == "Test CA"

def test_load_ca_certificate_missing(mock_root_ca_model: PlaceholderRootCA):
    mock_root_ca_model.certificate_pem = None
    with pytest.raises(ValueError, match="CA certificate PEM is missing"):
        load_ca_certificate(mock_root_ca_model)

def test_load_ca_certificate_invalid_pem(mock_root_ca_model: PlaceholderRootCA):
    mock_root_ca_model.certificate_pem = "INVALID CERT DATA"
    with pytest.raises(ValueError, match="Failed to load CA certificate"):
        load_ca_certificate(mock_root_ca_model)


# --- Tests for generate_signed_certificate ---
def test_generate_signed_certificate_basic_properties(
    mock_cert_request_data: PlaceholderCertRequest,
    mock_ca_cert: x509.Certificate,
    mock_ca_key: rsa.RSAPrivateKey
):
    (user_key_pem, chain_pem, serial_hex, valid_from, valid_to, subject_dn_str) = \
        generate_signed_certificate(mock_cert_request_data, mock_ca_cert, mock_ca_key)

    assert isinstance(user_key_pem, str)
    assert user_key_pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert isinstance(chain_pem, str)
    assert chain_pem.startswith("-----BEGIN CERTIFICATE-----")
    assert chain_pem.count("-----BEGIN CERTIFICATE-----") == 2 # User cert + CA cert
    assert isinstance(serial_hex, str)
    assert len(serial_hex) > 0
    assert isinstance(valid_from, datetime.datetime)
    assert isinstance(valid_to, datetime.datetime)
    assert (valid_to - valid_from).days == 365 # Approximate, could be 364 due to time
    assert mock_cert_request_data.common_name in subject_dn_str

    # Load the generated certificate to inspect it
    signed_cert = x509.load_pem_x509_certificate(chain_pem.encode('utf-8')) # Loads first cert (user cert)
    assert signed_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == mock_cert_request_data.common_name
    assert signed_cert.issuer == mock_ca_cert.subject

def test_generate_signed_certificate_extensions(
    mock_cert_request_data: PlaceholderCertRequest,
    mock_ca_cert: x509.Certificate,
    mock_ca_key: rsa.RSAPrivateKey
):
    (_, chain_pem, _, _, _, _) = \
        generate_signed_certificate(mock_cert_request_data, mock_ca_cert, mock_ca_key)
    
    signed_cert = x509.load_pem_x509_certificate(chain_pem.encode('utf-8'))

    # SAN
    san_ext = signed_cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    dns_names = [name.value for name in san_ext.get_values_for_type(x509.DNSName)]
    ip_addrs = [str(ip.value) for ip in san_ext.get_values_for_type(x509.IPAddress)]
    assert set(dns_names) == set(mock_cert_request_data.sans["dns"])
    assert set(ip_addrs) == set(mock_cert_request_data.sans["ip"])
    
    # Basic Constraints
    bc_ext = signed_cert.extensions.get_extension_for_class(x509.BasicConstraints).value
    assert bc_ext.ca is False
    
    # EKU
    eku_ext = signed_cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
    expected_ekus = {ExtendedKeyUsageOID.SERVER_AUTHENTICATION, ExtendedKeyUsageOID.CLIENT_AUTHENTICATION}
    assert {oid for oid in eku_ext} == expected_ekus
    
    # Key Usage
    ku_ext = signed_cert.extensions.get_extension_for_class(x509.KeyUsage).value
    assert ku_ext.digital_signature is True
    assert ku_ext.key_encipherment is True
    assert ku_ext.key_cert_sign is False # Not a CA
    
    # SKI
    assert signed_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier) is not None
    
    # AKI
    assert signed_cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier) is not None

    # CRL DP
    if settings.CRL_DISTRIBUTION_POINT_URL:
        crl_dp_ext = signed_cert.extensions.get_extension_for_class(x509.CRLDistributionPoints).value
        assert len(crl_dp_ext) == 1
        assert isinstance(crl_dp_ext[0].full_name[0], x509.UniformResourceIdentifier)
        assert crl_dp_ext[0].full_name[0].value == settings.CRL_DISTRIBUTION_POINT_URL
    else:
        with pytest.raises(x509.ExtensionNotFound):
            signed_cert.extensions.get_extension_for_class(x509.CRLDistributionPoints)

def test_generate_signed_certificate_no_sans(
    mock_ca_cert: x509.Certificate,
    mock_ca_key: rsa.RSAPrivateKey
):
    # Create a request with no SANs
    req_no_sans = PlaceholderCertRequest()
    req_no_sans.common_name = "no-sans-example.com"
    req_no_sans.sans = None # Or {}

    (_, chain_pem, _, _, _, _) = \
        generate_signed_certificate(req_no_sans, mock_ca_cert, mock_ca_key)
    
    signed_cert = x509.load_pem_x509_certificate(chain_pem.encode('utf-8'))
    with pytest.raises(x509.ExtensionNotFound):
        signed_cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)

def test_generate_signed_certificate_subject_dn_format(
    mock_cert_request_data: PlaceholderCertRequest,
    mock_ca_cert: x509.Certificate,
    mock_ca_key: rsa.RSAPrivateKey
):
    *_, subject_dn_str = generate_signed_certificate(mock_cert_request_data, mock_ca_cert, mock_ca_key)
    # RFC4514 string format is like "CN=commonName,OU=orgUnit,..."
    assert f"CN={mock_cert_request_data.common_name}" in subject_dn_str.upper() # Case insensitive for CN=
    # Check if it's a valid RFC4514 string (simple check)
    assert "=" in subject_dn_str
    assert len(subject_dn_str) > 0
