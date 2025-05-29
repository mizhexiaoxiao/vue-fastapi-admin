import ldap
from ldap.ldapobject import SimpleLDAPObject
import logging
from app.settings.config import settings

logger = logging.getLogger(__name__)

def authenticate_ldap_user(username: str, password: str) -> dict | None:
    """
    Authenticates a user against an LDAP server and fetches their details.

    Args:
        username: The username to authenticate.
        password: The password for the username.

    Returns:
        A dictionary with user details if authentication is successful, None otherwise.
        Example: {'username': 'user', 'email': 'user@example.com', 'alias': 'User Name', 'is_superuser': False}
    """
    if not settings.LDAP_SERVER_URI:
        logger.info("LDAP authentication is disabled. LDAP_SERVER_URI is not set.")
        return None

    if not password: # LDAP library can hang with empty password
        logger.warning(f"Attempt to authenticate LDAP user {username} with empty password.")
        return None

    user_dn = f"{settings.LDAP_USER_LOGIN_ATTR}={username},{settings.LDAP_BASE_DN}"

    try:
        # Initialize LDAP connection
        # ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER) # For testing with self-signed certs
        conn: SimpleLDAPObject = ldap.initialize(settings.LDAP_SERVER_URI)
        conn.protocol_version = ldap.VERSION3
        conn.set_option(ldap.OPT_REFERRALS, 0) # Important for Active Directory

        # Attempt to bind with user credentials
        logger.info(f"Attempting LDAP bind for user DN: {user_dn}")
        conn.simple_bind_s(user_dn, password)
        logger.info(f"LDAP bind successful for user: {username}")

        search_filter = f"({settings.LDAP_USER_LOGIN_ATTR}={username})"
        attributes_to_fetch = []
        if settings.LDAP_USER_EMAIL_ATTR:
            attributes_to_fetch.append(settings.LDAP_USER_EMAIL_ATTR)
        if settings.LDAP_USER_FULLNAME_ATTR:
            attributes_to_fetch.append(settings.LDAP_USER_FULLNAME_ATTR)
        
        if settings.LDAP_ADMIN_GROUP_DN:
            attributes_to_fetch.append('memberOf') # Common attribute for group membership

        logger.debug(f"Searching LDAP with base='{settings.LDAP_BASE_DN}', filter='{search_filter}', attributes='{attributes_to_fetch}'")
        # Note: search_s might need different parameters depending on LDAP server (e.g. AD might prefer None for attributes to get all user attributes)
        results = conn.search_s(settings.LDAP_BASE_DN, ldap.SCOPE_SUBTREE, search_filter, attributes_to_fetch)
        
        if not results:
            logger.warning(f"LDAP user {username} authenticated but could not be found during search.")
            conn.unbind_s()
            return None

        user_entry_dn, user_attributes = results[0]
        logger.debug(f"LDAP search result for {username}: DN='{user_entry_dn}', Attributes='{user_attributes}'")

        email = user_attributes.get(settings.LDAP_USER_EMAIL_ATTR, [b''])[0].decode() if settings.LDAP_USER_EMAIL_ATTR else ""
        fullname = user_attributes.get(settings.LDAP_USER_FULLNAME_ATTR, [b''])[0].decode() if settings.LDAP_USER_FULLNAME_ATTR else username

        is_admin = False
        if settings.LDAP_ADMIN_GROUP_DN:
            member_of_groups = [group.decode().lower() for group in user_attributes.get('memberOf', [])]
            logger.debug(f"User {username} memberOf: {member_of_groups}")
            if settings.LDAP_ADMIN_GROUP_DN.lower() in member_of_groups:
                is_admin = True
                logger.info(f"User {username} is a member of the admin group: {settings.LDAP_ADMIN_GROUP_DN}")
        
        user_details = {
            'username': username,
            'email': email,
            'alias': fullname,
            'is_superuser': is_admin,
        }
        logger.info(f"Successfully fetched details for LDAP user: {username}, details: {user_details}")
        return user_details

    except ldap.INVALID_CREDENTIALS:
        logger.warning(f"Invalid LDAP credentials for user: {username} (DN: {user_dn})")
        return None
    except ldap.SERVER_DOWN:
        logger.error(f"LDAP server is down or unreachable: {settings.LDAP_SERVER_URI}")
        return None
    except ldap.LDAPError as e:
        logger.error(f"An LDAP error occurred for user {username}: {e}")
        if hasattr(e, 'args') and e.args:
            for i, arg_item in enumerate(e.args): # Renamed arg to arg_item to avoid conflict
                logger.error(f"LDAPError arg[{i}]: {arg_item}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during LDAP authentication for {username}: {e}")
        return None
    finally:
        if 'conn' in locals() and conn: # Ensure conn was initialized
            try:
                conn.unbind_s()
                logger.debug(f"LDAP connection unbound for {username}")
            except ldap.LDAPError as e:
                logger.error(f"Error unbinding LDAP connection for {username}: {e}")
            except NameError: # Handle if conn wasn't defined due to early error
                pass
