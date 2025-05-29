import datetime
import ipaddress
from typing import Tuple, Optional, List # Added Optional, List

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, AuthorityInformationAccessOID

# Assuming models are accessible, adjust path if necessary
# from app.models.certificates import RootCACertificate, CertificateRequest
# For now, to avoid circular dependencies or complex setup for this isolated util,
# we'll assume the model instances are passed in and have the necessary attributes.
# This means direct model imports are commented out for now.
# If this util were part of a larger Django/FastAPI app context, these imports would be fine.
from app.settings.config import settings

# Placeholder for model type hinting if not directly importing
class RootCACertificate: # Placeholder
    encrypted_private_key: Optional[str]
    certificate_pem: str

class CertificateRequest: # Placeholder
    common_name: str
    sans: Optional[dict]


def load_ca_private_key(ca_object: RootCACertificate) -> rsa.RSAPrivateKey:
    """
    Loads the CA's private key from the RootCACertificate object.
    
    TODO: CRITICAL SECURITY - The private key in ca_object.encrypted_private_key
    MUST be securely encrypted at rest (e.g., using Fernet with settings.SECRET_KEY)
    and decrypted here. For this subtask, we assume it's plain text PEM.
    """
    if not ca_object.encrypted_private_key:
        raise ValueError("CA private key is missing.")
    
    # TODO: Decrypt ca_object.encrypted_private_key here
    plain_pem_private_key = ca_object.encrypted_private_key 

    try:
        private_key = serialization.load_pem_private_key(
            plain_pem_private_key.encode('utf-8'),
            password=None  # Assuming no password if decrypted, or handle password if key itself is pwd-protected
        )
        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise TypeError("Loaded key is not an RSA private key.")
        return private_key
    except Exception as e:
        # Log error appropriately
        raise ValueError(f"Failed to load CA private key: {e}")


def load_ca_certificate(ca_object: RootCACertificate) -> x509.Certificate:
    """Loads the CA certificate from the RootCACertificate object."""
    if not ca_object.certificate_pem:
        raise ValueError("CA certificate PEM is missing.")
    try:
        ca_cert = x509.load_pem_x509_certificate(ca_object.certificate_pem.encode('utf-8'))
        return ca_cert
    except Exception as e:
        # Log error appropriately
        raise ValueError(f"Failed to load CA certificate: {e}")


def generate_signed_certificate(
    request_data: CertificateRequest, 
    issuer_ca_cert: x509.Certificate, 
    issuer_ca_key: rsa.RSAPrivateKey
) -> Tuple[str, str, str, datetime.datetime, datetime.datetime, str]:
    """
    Generates a new private key, and a signed certificate for the request.

    Returns:
        A tuple containing:
        - user_private_key_pem (str): PEM-encoded private key for the user/service.
        - full_chain_pem (str): PEM-encoded signed certificate + issuer CA certificate.
        - serial_number_hex (str): Serial number of the issued certificate in hex.
        - valid_from (datetime.datetime): Certificate validity start.
        - valid_to (datetime.datetime): Certificate validity end.
        - subject_dn_str (str): Subject Distinguished Name as a string.
    """

    # a. Generate User's Private Key
    user_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048  # Consider making key_size configurable
    )
    user_private_key_pem = user_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()  # Or a chosen algorithm if key needs to be stored encrypted
    ).decode('utf-8')

    # b. Prepare Certificate Subject and Issuer
    subject_name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, request_data.common_name)
        # Potentially add other OIDs like Organization (O), Country (C) etc. from request_data or config
    ])
    issuer_name = issuer_ca_cert.subject

    # c. Set Validity
    valid_from = datetime.datetime.now(datetime.timezone.utc)
    valid_to = valid_from + datetime.timedelta(days=365) # Consider making duration configurable

    # d. Generate Serial Number
    serial_number = x509.random_serial_number()

    # e. Build Certificate Extensions
    extensions = []

    # Subject Key Identifier (SKI)
    # The public key of the certificate being generated
    extensions.append(
        x509.SubjectKeyIdentifier.from_public_key(user_private_key.public_key())
    )

    # Authority Key Identifier (AKI)
    # From the issuer's public key. use_issuer_public_key=True is simpler
    # but spec recommends from_issuer_subject_key_identifier if issuer SKI is present.
    # For simplicity, we'll use from_issuer_public_key if SKI not found on issuer cert.
    try:
        issuer_ski = issuer_ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
        extensions.append(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(issuer_ski.value)
        )
    except x509.ExtensionNotFound:
        extensions.append(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_ca_cert.public_key())
        )
        
    # Subject Alternative Name (SAN)
    san_list: List[x509.GeneralName] = []
    if request_data.sans:
        for dns_name in request_data.sans.get('dns', []):
            san_list.append(x509.DNSName(dns_name))
        for ip_address_str in request_data.sans.get('ip', []):
            san_list.append(x509.IPAddress(ipaddress.ip_address(ip_address_str)))
    
    if san_list: # Only add SAN if there are names
        extensions.append(x509.SubjectAlternativeName(san_list))

    # Basic Constraints: CA=False
    extensions.append(x509.BasicConstraints(ca=False, path_length=None))

    # Enhanced Key Usage
    # Common usages: serverAuth, clientAuth. Make this configurable if needed.
    extensions.append(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTHENTICATION,
            ExtendedKeyUsageOID.CLIENT_AUTHENTICATION,
        ])
    )

    # Key Usage
    extensions.append(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False, # Typically False for TLS
            key_encipherment=True,   # For RSA key transport
            data_encipherment=False, # Typically False for TLS
            key_agreement=False,     # Typically False for RSA
            key_cert_sign=False,     # Not a CA cert
            crl_sign=False,          # Not signing CRLs
            encipher_only=False,
            decipher_only=False
        )
    )

    # CRL Distribution Points
    if settings.CRL_DISTRIBUTION_POINT_URL:
        crl_point = x509.DistributionPoint(
            full_name=[x509.UniformResourceIdentifier(settings.CRL_DISTRIBUTION_POINT_URL)],
            relative_name=None,
            reasons=None,
            crl_issuer=None # If None, implies issuer of this cert is issuer of CRL
        )
        extensions.append(x509.CRLDistributionPoints([crl_point]))
    
    # f. Create Certificate Builder
    builder = x509.CertificateBuilder().subject_name(
        subject_name
    ).issuer_name(
        issuer_name
    ).public_key(
        user_private_key.public_key()
    ).serial_number(
        serial_number
    ).not_valid_before(
        valid_from
    ).not_valid_after(
        valid_to
    )

    for ext in extensions:
        builder = builder.add_extension(ext.value, critical=ext.critical)
        
    # g. Sign Certificate
    signed_certificate = builder.sign(
        issuer_ca_key,
        hashes.SHA256() # Common modern choice
    )

    # h. Serialize Signed Certificate to PEM
    signed_certificate_pem = signed_certificate.public_bytes(
        serialization.Encoding.PEM
    ).decode('utf-8')

    # i. Form Full Chain PEM
    # This assumes issuer_ca_cert is the direct issuer.
    # If there's an intermediate chain for the issuer_ca_cert itself, it should be part of its PEM.
    full_chain_pem = signed_certificate_pem + issuer_ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    
    # j. Return values
    serial_number_hex = hex(signed_certificate.serial_number)[2:] # Remove "0x"
    subject_dn_str = signed_certificate.subject.rfc4514_string()

    return (
        user_private_key_pem,
        full_chain_pem,
        serial_number_hex,
        valid_from,
        valid_to,
        subject_dn_str
    )

# Example usage (for testing, not part of app flow)
if __name__ == '__main__':
    # This example won't run without actual CA key/cert data and model instances.
    # It's conceptual to illustrate the structure.
    print("Certificate utility functions defined.")
    print(f"CRL Distribution Point URL from settings: {settings.CRL_DISTRIBUTION_POINT_URL}")

    # --- Mock CA Data for conceptual testing ---
    # In a real scenario, this would come from the database via RootCACertificate model
    mock_ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    mock_ca_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Mock CA")])
    mock_ca_builder = x509.CertificateBuilder().subject_name(
        mock_ca_subject
    ).issuer_name(
        mock_ca_subject # Self-signed
    ).public_key(
        mock_ca_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365*5)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True
    )
    mock_ca_cert_obj = mock_ca_builder.sign(mock_ca_key, hashes.SHA256())
    
    mock_ca_pem = mock_ca_cert_obj.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    mock_ca_key_pem = mock_ca_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Mock RootCACertificate model instance
    class MockRootCACert(RootCACertificate):
        def __init__(self, cert_pem, key_pem):
            self.certificate_pem = cert_pem
            self.encrypted_private_key = key_pem # Plain text for mock

    mock_ca_model_instance = MockRootCACert(mock_ca_pem, mock_ca_key_pem)

    # Mock CertificateRequest model instance
    class MockCertRequest(CertificateRequest):
        def __init__(self, cn, sans_data=None):
            self.common_name = cn
            self.sans = sans_data if sans_data else {}
            
    mock_req_data = MockCertRequest(
        common_name="test.example.com",
        sans_data={"dns": ["test.example.com", "www.test.example.com"], "ip": ["192.168.1.100"]}
    )

    print("\n--- Conceptual Test ---")
    try:
        loaded_key = load_ca_private_key(mock_ca_model_instance)
        print(f"CA Private Key loaded: {isinstance(loaded_key, rsa.RSAPrivateKey)}")
        loaded_cert = load_ca_certificate(mock_ca_model_instance)
        print(f"CA Certificate loaded: {isinstance(loaded_cert, x509.Certificate)}")

        (user_key_pem, chain_pem, sn_hex, vf, vt, sub_dn) = generate_signed_certificate(
            mock_req_data, loaded_cert, loaded_key
        )
        print("\nGenerated Certificate Details:")
        print(f"  Subject DN: {sub_dn}")
        print(f"  Serial (hex): {sn_hex}")
        print(f"  Valid From: {vf}")
        print(f"  Valid To: {vt}")
        # print(f"  User Key PEM:\n{user_key_pem}")
        # print(f"  Full Chain PEM:\n{chain_pem}")
        print("Conceptual test completed.")
    except Exception as e:
        print(f"Conceptual test error: {e}")
