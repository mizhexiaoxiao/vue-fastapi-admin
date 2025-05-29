from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec # For loading various private key types
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta, timezone
import ipaddress
import os # For random serial number generation

from app.settings.config import settings
import logging

logger = logging.getLogger(__name__)

def load_ca_resources():
    """
    Reads the PEM encoded CA certificate and private key.
    Handles decryption if a password is provided.

    Returns:
        Tuple (x509.Certificate, private_key_object) or (None, None) if errors occur.
    """
    ca_cert = None
    ca_private_key = None

    if not settings.CA_CERT_PATH or not settings.CA_PRIVATE_KEY_PATH:
        logger.error("CA_CERT_PATH or CA_PRIVATE_KEY_PATH not configured in settings.")
        return None, None

    try:
        with open(settings.CA_CERT_PATH, "rb") as f:
            ca_cert_pem = f.read()
        ca_cert = x509.load_pem_x509_certificate(ca_cert_pem, default_backend())
        logger.info(f"Successfully loaded CA certificate from {settings.CA_CERT_PATH}")
    except FileNotFoundError:
        logger.error(f"CA certificate file not found at: {settings.CA_CERT_PATH}")
        return None, None
    except ValueError as e:
        logger.error(f"Error loading CA certificate: {e}")
        return None, None

    try:
        with open(settings.CA_PRIVATE_KEY_PATH, "rb") as f:
            ca_private_key_pem = f.read()
        
        password_bytes = None
        if settings.CA_PRIVATE_KEY_PASSWORD:
            password_bytes = settings.CA_PRIVATE_KEY_PASSWORD.encode()

        ca_private_key = serialization.load_pem_private_key(
            ca_private_key_pem,
            password=password_bytes,
            backend=default_backend()
        )
        logger.info(f"Successfully loaded CA private key from {settings.CA_PRIVATE_KEY_PATH}")
    except FileNotFoundError:
        logger.error(f"CA private key file not found at: {settings.CA_PRIVATE_KEY_PATH}")
        return None, None
    except (TypeError, ValueError) as e: # TypeError for incorrect password, ValueError for bad key format
        logger.error(f"Error loading CA private key (check format or password): {e}")
        return None, None
    
    return ca_cert, ca_private_key

def generate_x509_certificate(
    user_common_name: str, 
    subject_alt_names_data: list[str], 
    ekus_data: list[str], 
    requested_days: int, 
    public_key_pem: str
):
    """
    Generates an X.509 certificate signed by the configured CA.
    """
    ca_cert, ca_private_key = load_ca_resources()
    if not ca_cert or not ca_private_key:
        logger.error("Failed to generate certificate: CA resources not loaded.")
        return None

    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
    except ValueError as e:
        logger.error(f"Invalid public key PEM provided: {e}")
        return None

    builder = x509.CertificateBuilder()
    
    # Subject Name
    subject_name_attributes = [x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, user_common_name)]
    builder = builder.subject_name(x509.Name(subject_name_attributes))
    
    # Issuer Name (from CA certificate)
    builder = builder.issuer_name(ca_cert.subject)

    # Public Key
    builder = builder.public_key(public_key)

    # Serial Number (random large integer)
    builder = builder.serial_number(int.from_bytes(os.urandom(16), 'big'))

    # Validity
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(days=requested_days)
    builder = builder.not_valid_before(start_time)
    builder = builder.not_valid_after(end_time)

    # Basic Constraints (cA=False, critical)
    builder = builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True
    )

    # Subject Alternative Names (SANs)
    sans = []
    if subject_alt_names_data:
        for san_entry in subject_alt_names_data:
            try:
                name_type, value = san_entry.split(":", 1)
                if name_type.lower() == "dns":
                    sans.append(x509.DNSName(value))
                elif name_type.lower() == "ip":
                    sans.append(x509.IPAddress(ipaddress.ip_address(value)))
                else:
                    logger.warning(f"Unsupported SAN type: {name_type} in entry: {san_entry}")
            except ValueError as e:
                logger.warning(f"Invalid SAN entry '{san_entry}': {e}")
                continue # Skip invalid SAN entry
    if sans: # Only add SAN extension if there are valid SANs
      builder = builder.add_extension(x509.SubjectAlternativeName(sans), critical=True) # Typically critical

    # Extended Key Usages (EKUs)
    ekus = []
    if ekus_data:
        for eku_oid_str in ekus_data:
            try:
                ekus.append(x509.ObjectIdentifier(eku_oid_str))
            except ValueError as e: # Should not happen if OIDs are validated before
                logger.warning(f"Invalid EKU OID string: {eku_oid_str} - {e}")
                continue
    if ekus: # Only add EKU extension if there are valid EKUs
      builder = builder.add_extension(x509.ExtendedKeyUsage(ekus), critical=False)


    # Key Usage (example: digital signature, key encipherment for TLS)
    # This is often required by CAs and clients.
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True, # For RSA key exchange
            content_commitment=False, 
            data_encipherment=False, 
            key_agreement=False, # For Diffie-Hellman
            key_cert_sign=False, 
            crl_sign=False, 
            encipher_only=False, 
            decipher_only=False
        ),
        critical=True, # Often critical
    )
    
    # Sign the certificate
    try:
        certificate = builder.sign(
            private_key=ca_private_key,
            algorithm=hashes.SHA256(),
            backend=default_backend()
        )
        logger.info(f"Successfully generated and signed certificate for CN: {user_common_name}")
    except Exception as e: # Catch broad exceptions during signing
        logger.error(f"Error signing certificate for CN {user_common_name}: {e}")
        return None

    return certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')


def convert_pem_to_pfx(user_pem_cert_chain_str: str, user_private_key_pem_str: str, pfx_password: str | None):
    """
    Converts PEM encoded certificate (chain) and private key to PFX format.
    """
    certs = []
    try:
        # Load all certificates from the chain string
        # x509.load_pem_x509_certificates is not a standard method.
        # We need to split PEMs if they are concatenated.
        pem_blobs = user_pem_cert_chain_str.strip().split("-----END CERTIFICATE-----")
        for pem_blob in pem_blobs:
            if pem_blob.strip():
                full_pem = pem_blob.strip() + "\n-----END CERTIFICATE-----"
                certs.append(x509.load_pem_x509_certificate(full_pem.encode(), default_backend()))
        
        if not certs:
            logger.error("No certificates found in user_pem_cert_chain_str.")
            return None
        user_cert = certs[0] # The first one is the user's certificate
        ca_certs = certs[1:] if len(certs) > 1 else []

    except ValueError as e:
        logger.error(f"Error parsing certificate PEM data: {e}")
        return None

    try:
        private_key = serialization.load_pem_private_key(
            user_private_key_pem_str.encode(),
            password=None, # Assuming user's private key for PFX is not password protected at this stage
            backend=default_backend()
        )
    except ValueError as e:
        logger.error(f"Error parsing private key PEM data: {e}")
        return None

    if not pfx_password:
        logger.warning("PFX password is not provided. PFX will be unencrypted (if library allows) or use a default.")
        # Some libraries might require a password. Using a default or handling this case.
        # For simplicity, if no password, we'll attempt to create it without encryption if possible,
        # or the library might default to a trivial one if it requires one.
        # The `serialize_key_and_certificates` takes password bytes.
        # If password is None, then no encryption is requested for the private key.
        encryption_algorithm = serialization.NoEncryption()
        password_bytes_for_pfx = None

    else:
        password_bytes_for_pfx = pfx_password.encode()
        encryption_algorithm = serialization.BestAvailableEncryption(password_bytes_for_pfx)


    try:
        pfx_data = serialization.pkcs12.serialize_key_and_certificates(
            name=user_cert.subject.rfc4514_string().encode('utf-8'), # Friendly name for the PFX bundle
            key=private_key,
            cert=user_cert,
            cas=ca_certs if ca_certs else None, # Must be None if empty, not an empty list
            encryption_algorithm=encryption_algorithm
        )
        logger.info(f"Successfully created PFX bundle for certificate: {user_cert.subject.rfc4514_string()}")
        return pfx_data
    except Exception as e:
        logger.error(f"Error creating PFX bundle: {e}")
        return None

if __name__ == '__main__':
    # This section is for basic testing and demonstration.
    # It requires placeholder CA files to be set up.
    # To run this, you would need to:
    # 1. Create dummy CA_CERT_PATH and CA_PRIVATE_KEY_PATH files.
    #    E.g., using OpenSSL:
    #    openssl genpkey -algorithm RSA -out ca_private_key.pem -aes256 -pass pass:testcapass
    #    openssl req -new -x509 -key ca_private_key.pem -out ca_cert.pem -days 3650 -subj "/CN=Test Root CA" -passin pass:testcapass
    # 2. Update settings object or mock it.
    
    logging.basicConfig(level=logging.INFO)

    class MockSettings:
        CA_CERT_PATH = "ca_cert.pem"  # Replace with actual path to your dummy CA cert
        CA_PRIVATE_KEY_PATH = "ca_private_key.pem"  # Replace with actual path to your dummy CA key
        CA_PRIVATE_KEY_PASSWORD = "testcapass" # Or None if not encrypted

    # settings = MockSettings() # Uncomment and adjust paths to test

    # Example: Generate a key pair for the user (normally client would do this)
    # user_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    # user_public_key = user_private_key.public_key()
    # user_public_key_pem = user_public_key.public_bytes(
    #     encoding=serialization.Encoding.PEM,
    #     format=serialization.PublicFormat.SubjectPublicKeyInfo
    # ).decode('utf-8')
    # user_private_key_pem = user_private_key.private_bytes(
    #    encoding=serialization.Encoding.PEM,
    #    format=serialization.PrivateFormat.PKCS8,
    #    encryption_algorithm=serialization.NoEncryption()
    # ).decode('utf-8')

    # print("Generated User Public Key PEM:\n", user_public_key_pem)
    # print("\nGenerated User Private Key PEM (for PFX testing):\n", user_private_key_pem)

    # # Test certificate generation (requires CA files and public key)
    # if os.path.exists(settings.CA_CERT_PATH) and os.path.exists(settings.CA_PRIVATE_KEY_PATH):
    #     logger.info("Attempting to generate certificate...")
    #     generated_cert_pem = generate_x509_certificate(
    #         user_common_name="testuser.example.com",
    #         subject_alt_names_data=["dns:testuser.example.com", "dns:alt.example.com", "ip:192.168.1.100"],
    #         ekus_data=["1.3.6.1.5.5.7.3.1", "1.3.6.1.5.5.7.3.2"], # Server Auth, Client Auth
    #         requested_days=30,
    #         public_key_pem=user_public_key_pem 
    #     )
    #     if generated_cert_pem:
    #         logger.info("Generated Certificate PEM:\n" + generated_cert_pem)

    #         # Test PFX conversion (requires generated cert and private key)
    #         # For a full chain, you'd append CA certs to generated_cert_pem
    #         # For this test, assume generated_cert_pem is just the user cert.
    #         # We'd typically add the CA cert to the chain for PFX.
            
    #         ca_cert_obj, _ = load_ca_resources()
    #         full_chain_pem = generated_cert_pem
    #         if ca_cert_obj:
    #             full_chain_pem += "\n" + ca_cert_obj.public_bytes(serialization.Encoding.PEM).decode('utf-8')


    #         logger.info("\nAttempting to generate PFX...")
    #         pfx_bytes = convert_pem_to_pfx(
    #             user_pem_cert_chain_str=full_chain_pem, 
    #             user_private_key_pem_str=user_private_key_pem, 
    #             pfx_password="testpfxpassword"
    #         )
    #         if pfx_bytes:
    #             with open("test_cert.pfx", "wb") as f:
    #                 f.write(pfx_bytes)
    #             logger.info("PFX file generated: test_cert.pfx")
    #         else:
    #             logger.error("PFX generation failed.")
    #     else:
    #         logger.error("Certificate generation failed.")
    # else:
    #     logger.warning(f"Skipping advanced tests: CA files not found at configured paths ({settings.CA_CERT_PATH}, {settings.CA_PRIVATE_KEY_PATH}).")
    pass
