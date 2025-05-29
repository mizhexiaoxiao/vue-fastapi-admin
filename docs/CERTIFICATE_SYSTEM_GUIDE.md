# Digital Certificate Management System Guide

## 1. Overview
The Digital Certificate Management System is designed to manage the lifecycle of digital certificates within the application. This includes handling user requests for new certificates, allowing administrators to approve or reject these requests, issuing certificates using an admin-configured internal Certificate Authority (CA), and enabling users to download their issued certificates and corresponding private keys.

The system defines two primary roles:
-   **User:** Can request certificates and download their own issued certificates.
-   **Administrator:** Manages the system's Root CAs, processes certificate requests (approve/reject), and can view all system components.

## 2. API Documentation
- The system's API is documented via FastAPI's automatic OpenAPI generation.
- Access it at `/docs` (Swagger UI) and `/redoc` (ReDoc UI) when the application is running.
- **Recommendation:** Review all API endpoint descriptions (summaries, descriptions in Python docstrings), Pydantic model field descriptions (`description` attribute in `Field`), and response model examples in the Python code (`app/api/v1/certificates_api.py`, `app/schemas/certificates.py`) to ensure they are clear and informative for API users. These descriptions automatically populate the OpenAPI documentation.

## 3. For Administrators

### 3.1. LDAP Configuration
- To enable LDAP authentication (which is currently mocked for `ldapuser`), configure the following settings in `app/settings/config.py` (or via environment variables):
  - `LDAP_SERVER_URI`: e.g., "ldap://your-ldap-server:389"
  - `LDAP_BIND_DN`: e.g., "cn=admin,dc=example,dc=com"
  - `LDAP_BIND_PASSWORD`: Password for the Bind DN.
  - `LDAP_USER_SEARCH_BASE`: e.g., "ou=users,dc=example,dc=com"
  - `LDAP_USER_SEARCH_FILTER`: e.g., "(uid=%s)"
  - `LDAP_ATTR_USERNAME`: LDAP attribute for username (e.g., "uid").
  - `LDAP_ATTR_EMAIL`: LDAP attribute for email (e.g., "mail").
  - `LDAP_ATTR_FIRST_NAME`: LDAP attribute for first name (e.g., "givenName").
  - `LDAP_ATTR_LAST_NAME`: LDAP attribute for last name (e.g., "sn").
- After configuration, the mock LDAP implementation in `app/core/auth/ldap_mock.py` and the login endpoint in `app/api/v1/base/base.py` would need to be updated to use a real LDAP library (e.g., `ldap3`) and interact with the configured LDAP server.

### 3.2. Issuing CA Setup
1.  **Upload CA Certificate (and Private Key if for signing):**
    - Use the `POST /api/v1/certificates/root_ca` endpoint.
    - Provide:
      - `name` (string): A descriptive name for this CA (e.g., "Internal Corporate CA G1").
      - `certificate_pem` (string): The PEM-encoded CA certificate. This can be a single certificate or a chain (Root CA cert + Intermediate CA certs, if any, concatenated).
      - `private_key_pem` (string, Optional): The PEM-encoded private key for this CA *only if this CA will be used by the system to sign new certificates*. If this CA is for reference or trust validation only, the private key is not needed.
      - `is_issuer` (boolean, Optional, default: `false`): Set to `false` initially. You will designate an active issuer in a separate step.
    - **SECURITY WARNING:** Currently, if `private_key_pem` is provided, it is stored **as plain text** in the database (`RootCACertificate.encrypted_private_key` field). This is **NOT SECURE** for production environments. Future development must ensure this key is encrypted at rest (e.g., using Fernet with the application's `SECRET_KEY` or a dedicated Hardware Security Module (HSM)). The `TODO` comments in the API implementation (`app/api/v1/certificates_api.py`) and cryptographic utilities (`app/core/certificate_utils.py`) highlight this critical security gap.
2.  **Designate Active Issuer:**
    - Use the `PUT /api/v1/certificates/root_ca/{ca_id}` endpoint for the CA you wish to use for signing.
    - In the request body, set `is_issuer: true`.
    - Only one CA should typically be marked as `is_issuer: true`. The system currently uses the first CA it finds with this flag set.
    - **Crucially, the CA designated as `is_issuer` must have its private key uploaded and stored (even if currently in plain text).** The system will fail to sign certificates if the active issuer CA does not have its private key available.

### 3.3. Managing Certificate Requests
- **List All Requests:** `GET /api/v1/certificates/requests/admin`
  - View all certificate requests submitted by users.
- **Approve a Request:** `POST /api/v1/certificates/requests/{request_id}/approve`
  - `{request_id}` is the ID of the pending certificate request.
  - This action uses the currently designated active issuing CA (see section 3.2) to sign and issue a new digital certificate based on the request details.
  - The `CertificateRequest` status is updated to "approved".
  - An `IssuedCertificate` record is created.
- **Reject a Request:** `POST /api/v1/certificates/requests/{request_id}/reject`
  - `{request_id}` is the ID of the pending certificate request.
  - Request body requires: `{"status": "rejected", "rejection_reason": "Your reason here"}`.
  - The `CertificateRequest` status is updated to "rejected", and the reason is stored.

### 3.4. Managing Issued Certificates
- **List Issued Certificates:**
  - An endpoint like `GET /api/v1/certificates/issued_certificates/admin` would be beneficial for admins to view all issued certificates.
  - **TODO:** This endpoint is not yet implemented. (Verify in `app/api/v1/certificates_api.py` and add if missing).
- **Revoke an Issued Certificate:**
  - An endpoint like `POST /api/v1/certificates/issued_certificates/{certificate_id}/revoke` would be needed.
  - This should update the `IssuedCertificate.status` to "revoked", set `revoked_at`, and store a `revocation_reason`.
  - **TODO:** This endpoint is not yet implemented.
  - **Note on CRL/OCSP:** Simply marking a certificate as "revoked" in the database does not make it invalid for clients that rely on CRLs or OCSP. A proper revocation system requires generating and publishing updated Certificate Revocation Lists (CRLs) or implementing an Online Certificate Status Protocol (OCSP) responder. The current `CRL_DISTRIBUTION_POINT_URL` in certificates is a placeholder.

## 4. For Users

### 4.1. Requesting a Certificate
- Use the `POST /api/v1/certificates/requests` endpoint.
- Provide in the request body:
  - `common_name` (string): Your desired common name for the certificate (e.g., "my.device.example.com", "John Doe VPN").
  - `sans` (object, Optional): A dictionary of Subject Alternative Names.
    - Example: `{"dns": ["alt.my.device.com", "service.example.net"], "ip": ["192.168.1.10"]}`
    - Supported keys: `"dns"` (for DNS names) and `"ip"` (for IP addresses). Values are lists of strings.
- Your request will be submitted with a "pending" status and awaits administrator review.

### 4.2. Checking Request Status
- Use the `GET /api/v1/certificates/requests` endpoint.
- This will list all certificate requests you have submitted and their current status (e.g., "pending", "approved", "rejected").

### 4.3. Downloading Your Approved Certificate
- Once your request is "approved", an `IssuedCertificate` record is created.
- To download it:
  1. You first need the ID of the *issued certificate*. This ID should ideally be made available when you list your approved requests or view a specific approved request's details. **TODO:** The API response for an approved `CertificateRequestRead` might need to be enhanced to include the ID of the corresponding `IssuedCertificate`.
  2. Use the `GET /api/v1/certificates/issued_certificates/{certificate_id}/download` endpoint, replacing `{certificate_id}` with the actual ID.
- The response will be a JSON object containing:
  - `certificate_pem` (string): The issued certificate in PEM format, including the chain up to the issuing CA.
  - `private_key_pem` (string): Your corresponding private key, also in PEM format.
- **SECURITY NOTE:** You are responsible for protecting your downloaded private key. It is provided to you in plain text format. Store it securely.

## 5. Future Security Enhancements (TODOs)
This system provides basic certificate management functionality. For production use, several critical security enhancements are necessary:
- **Secure Storage of CA Private Keys:**
  - The `encrypted_private_key` field in the `RootCACertificate` model currently stores the CA's private key in plain text if provided.
  - **Action:** Implement strong encryption (e.g., AES-GCM via Fernet using the application's `SECRET_KEY`, or integration with a Hardware Security Module - HSM) for this key at rest. Update `app/core/certificate_utils.py` (`load_ca_private_key`) and the CA upload/update API endpoints to handle encryption/decryption.
- **Secure Storage of User Private Keys:**
  - The `encrypted_private_key` field in the `IssuedCertificate` model is intended to store the user's private key if generated by the system. Currently, it's stored in plain text.
  - **Action:** If the system stores user private keys, these must also be encrypted at rest using a strong mechanism. The download endpoint would then need to decrypt the key before providing it to the user. Consider if the system should even store user private keys or if they should be generated client-side with a CSR (Certificate Signing Request) mechanism for higher security (though this adds complexity).
- **Certificate Revocation List (CRL) / OCSP:**
  - The `CRL_DISTRIBUTION_POINT_URL` is added to issued certificates, but the system does not currently generate or publish CRLs.
  - **Action:** Implement a mechanism to generate and periodically publish CRLs if this revocation method is chosen. Alternatively, implement an OCSP responder. This is crucial for a complete PKI lifecycle.
- **Input Validation and Sanitization:**
  - Ensure all inputs (especially Common Name, SANs) are rigorously validated to prevent injection attacks or abuse (e.g., requesting certificates for domains not owned by the user, if applicable to the policy).
- **Audit Trails:**
  - Enhance audit logging for all critical actions within the certificate management system (CA creation/updates, request approval/rejection, certificate issuance/revocation). The existing `HttpAuditLogMiddleware` provides a base, but more detailed application-level logging might be needed.
- **Role and Permission Refinements:**
  - Review and refine permissions as the system evolves to ensure least privilege.
- **Configuration Management:**
  - Move sensitive configurations (like `SECRET_KEY`) and potentially LDAP credentials strictly to environment variables or a secure configuration management system, rather than hardcoding in `config.py` defaults.
```
