# Vue FastAPI Admin - Certificate Management System

This project is an extension of the vue-fastapi-admin boilerplate, enhanced with a comprehensive Digital Certificate Management System designed for enterprise use.

## Core Features (Original Vue FastAPI Admin)

*   Standard vue-fastapi-admin features including:
*   User Management
*   Role & Permission Management
*   API Endpoint Control (via UI)
*   Department Management
*   Menu Management
*   FastAPI Backend with Tortoise ORM
*   Vue.js Frontend (Vue 3, Vite)
*   Authentication (JWT based, with initial superuser setup)
*   Audit Logging

## Certificate Management System Features

This system allows users to request digital certificates and administrators to manage the issuance process and Certificate Authorities.

*   **LDAP Authentication:** Integrates with an LDAP directory for user authentication (configurable).
*   **User Certificate Requests:**
    *   Users can submit requests for X.509 certificates via a form.
    *   Support for Subject Alternative Name (SAN) extensions (DNS names, IP addresses).
    *   Support for Enhanced Key Usage (EKU) extensions (common and custom OIDs).
    *   Users provide their own Public Key (PEM format).
*   **Admin Approval Workflow:**
    *   Administrators review pending certificate requests.
    *   Requests can be approved (leading to certificate issuance) or rejected with a reason.
*   **Certificate Issuance:**
    *   Generated certificates include SAN and EKU extensions as requested.
    *   Issued certificates are signed by a configurable internal Certificate Authority.
*   **CA Management (Admin):**
    *   Admins can upload and manage the root and intermediate CA certificates (as PEM data).
    *   Support for a chain of trust (CA bundle in PEM format can be stored).
    *   Admins can designate the active signing CA from the managed CAs.
*   **Certificate Download:**
    *   Users can download their issued certificates in PEM format.
    *   The downloaded PEM typically includes the full certificate chain as provided by the CA.
*   **PEM to PFX Conversion Utility:**
    *   A tool for users to convert PEM-formatted certificates (with their private key) into PFX format.
    *   The PFX file is password-protected with the user's username.
*   **Role-Based Access Control:**
    *   Distinct functionalities for regular users and administrators.
    *   New navigation menus for "Certificate Services", "Tools" (user-facing), and "Certificate Admin" (admin-facing, under System Management).

## Tech Stack

*   **Backend:** FastAPI, Tortoise ORM, Python 3.11
*   **Frontend:** Vue.js 3, Vite, Pinia
*   **Database:** Configured for MySQL (requires user setup). SQLite is the default in the original boilerplate but this version targets MySQL.
*   **Certificate Operations:** `cryptography` library (Python)
*   **Migrations:** `aerich`

## Setup and Configuration

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url> # Replace with the actual URL
    cd <repository_directory>  # Replace with the actual directory name
    ```

2.  **Install Dependencies:**
    *   **Backend:** Ensure Python 3.11 is installed and accessible (e.g., via `python3`). Then, from the project root:
        ```bash
        python3 -m pip install -r requirements.txt
        ```
        (Note: If `python-ldap` fails to build, ensure system dependencies like `libldap2-dev`, `libsasl2-dev`, `libssl-dev`, and `python3.11-dev` are installed.)
    *   **Frontend:** Navigate to the `web/` directory:
        ```bash
        cd web
        npm install # or yarn install / pnpm install
        cd ..
        ```

3.  **Configuration (`app/settings/config.py`):**
    *   **Database (MySQL):**
        *   Locate the global `TORTOISE_ORM` dictionary.
        *   Update the `"mysql"` connection settings with your MySQL server details (host, port, user, password, database name). The database must exist on your server.
        *   Example placeholder:
          ```python
          "mysql": {
              "engine": "tortoise.backends.mysql",
              "credentials": {
                  "host": "localhost",
                  "port": 3306,
                  "user": "yourusername_placeholder",
                  "password": "yourpassword_placeholder",
                  "database": "yourdatabase_placeholder",
              },
          },
          ```
        *   Ensure `"default_connection": "mysql"` is set within `TORTOISE_ORM["apps"]["models"]`.
    *   **LDAP Authentication:**
        *   In the `Settings` class, configure `LDAP_SERVER_URI`, `LDAP_BASE_DN`, and other `LDAP_*` settings as per your LDAP directory structure. If `LDAP_SERVER_URI` is empty, LDAP authentication is skipped.
    *   **Initial Certificate Authority (CA):**
        *   In the `Settings` class, set `CA_CERT_PATH` to the absolute path of your root CA certificate PEM file.
        *   Set `CA_PRIVATE_KEY_PATH` to the absolute path of your root CA's private key PEM file.
        *   Set `CA_PRIVATE_KEY_PASSWORD` if the private key is encrypted (set to `None` or an empty string if not).
        *   **Security Note:** Protect your CA private key diligently. In a production environment, consider using a Hardware Security Module (HSM) or other secure key storage solutions. These paths are used by the `generate_x509_certificate` function if no CA is configured via the CA Management UI or if that logic defaults to these settings.

4.  **Database Migrations:**
    *   The Aerich configuration is stored in `pyproject.toml` (created/updated by `aerich init`).
    *   Once the database connection is configured in `app/settings/config.py`:
        1.  Initialize the database for Aerich (creates the `aerich` table):
            ```bash
            # Run from project root (/app)
            python3 -m aerich init-db 
            ```
            (This command will fail if the database specified in `config.py` is not accessible. Ensure your MySQL server is running and credentials are correct.)
        2.  Generate migration files based on your models:
            ```bash
            python3 -m aerich migrate --name initial_migration # Or a more descriptive name
            ```
        3.  Apply the migrations to the database:
            ```bash
            python3 -m aerich upgrade
            ```
    *   This sequence will create all necessary tables, including those for the certificate management system.

5.  **Run the Application:**
    *   **Backend:** From the project root:
        ```bash
        python run.py
        ```
        (This script also attempts to run `init_data()` which includes `init_db()` for Aerich, superuser creation, and initial menu/role setup.)
    *   **Frontend (Development Server):** From the `web/` directory:
        ```bash
        npm run dev
        ```

## Using the Certificate Management System

*   **Users:**
    *   Log in (using LDAP credentials if configured and enabled, otherwise using local DB credentials like `admin`/`123456` for the initial superuser).
    *   Navigate to "Certificate Services" > "Request New Certificate" to submit a CSR by providing details and a PEM-encoded public key.
    *   View status of their requests under "Certificate Services" > "My Certificate Requests".
    *   Download issued certificates (as PEM files) from the "My Certificate Requests" page.
    *   Use "Tools" > "PEM to PFX Converter" to convert their downloaded certificate and corresponding private key into a PFX file (password is their username).
*   **Administrators:**
    *   Log in (must be a superuser or belong to an admin group if LDAP admin checks are implemented).
    *   Navigate to "System Management" > "Certificate Admin" to:
        *   "Manage Cert Requests": View all requests, filter by status, approve or reject pending requests.
        *   "Manage CAs": Upload new CA certificates (PEM format), view details of existing CAs, and set one CA as the "Active Root" for signing new certificates.

## API Endpoints

The system introduces new API endpoints under the following base paths. Refer to the FastAPI router definitions in `app/api/v1/` for detailed endpoint specifications and request/response models.

*   **Certificate Requests (User & Admin Actions):** `/api/v1/certificate-requests/`
    *   `POST /`: User submits a new certificate request.
    *   `GET /`: User lists their own certificate requests.
    *   `GET /admin/`: Admin lists all certificate requests (with filtering).
    *   `POST /admin/{request_id}/action`: Admin approves or rejects a request.
*   **Issued Certificates (User Actions):** `/api/v1/issued-certificates/`
    *   `GET /`: User lists their own issued certificates.
    *   `GET /{issued_certificate_id}/download`: User downloads a specific issued certificate (PEM format).
*   **CA Management (Admin Actions):** `/api/v1/ca-management/`
    *   `POST /`: Admin creates/uploads a new CA.
    *   `GET /`: Admin lists all CAs.
    *   `GET /{ca_id}`: Admin gets details of a specific CA.
    *   `PUT /{ca_id}`: Admin updates a CA (e.g., to set as active root).
    *   `DELETE /{ca_id}`: Admin deletes a CA.
*   **Certificate Utilities (User Actions):** `/api/v1/certificate-utils/`
    *   `POST /pem-to-pfx`: User converts PEM certificate chain and private key to PFX.

```
