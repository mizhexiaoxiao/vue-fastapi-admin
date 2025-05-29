from tortoise import fields
from app.models.base import BaseModel, TimestampMixin
from app.models.admin import User # For ForeignKey relationship

class CertificateAuthority(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=100, unique=True, description="CA Name (e.g., Root CA, Intermediate CA 1)")
    description = fields.TextField(null=True, description="Description of the CA")
    pem_data = fields.TextField(description="PEM encoded certificate data of the CA. If it's a bundle, it includes the chain.")
    is_active_root = fields.BooleanField(default=False, description="Indicates if this is the currently active root CA for signing new certificates.")
    expires_at = fields.DatetimeField(null=True, description="CA Certificate Expiry Date")

    class Meta:
        table = "certificate_authority"

    def __str__(self):
        return self.name

class CertificateRequest(BaseModel, TimestampMixin):
    user = fields.ForeignKeyField("models.User", related_name="certificate_requests", description="Requesting User")
    common_name = fields.CharField(max_length=255, description="Common Name (CN)")
    distinguished_name_json = fields.JSONField(null=True, description="Full DN details in JSON (e.g., O, OU, L, ST, C)")
    sans = fields.JSONField(null=True, description="Subject Alternative Names (JSON array of strings, e.g., ['dns:example.com', 'ip:1.2.3.4'])")
    ekus = fields.JSONField(null=True, description="Enhanced Key Usages (JSON array of OID strings or friendly names)")
    status = fields.CharField(max_length=20, default="pending", description="Request Status (e.g., pending, approved, rejected, issued)")
    rejection_reason = fields.TextField(null=True, description="Reason for rejection")
    requested_days = fields.IntField(default=365, description="Requested validity period in days")
    approved_at = fields.DatetimeField(null=True, description="Timestamp of approval")

    class Meta:
        table = "certificate_request"

    def __str__(self):
        return f"{self.common_name} (User: {self.user_id}, Status: {self.status})"

class IssuedCertificate(BaseModel, TimestampMixin):
    request = fields.OneToOneField("models.CertificateRequest", related_name="issued_certificate", on_delete=fields.CASCADE, description="Original Certificate Request")
    user = fields.ForeignKeyField("models.User", related_name="issued_certificates", on_delete=fields.SET_NULL, null=True, description="Certificate Owner (denormalized, request has user too)")
    serial_number = fields.CharField(max_length=100, unique=True, description="Certificate Serial Number")
    pem_data = fields.TextField(description="PEM encoded certificate data (including chain)")
    issued_at = fields.DatetimeField(auto_now_add=True, description="Issuance Timestamp")
    expires_at = fields.DatetimeField(description="Certificate Expiry Date")
    revoked_at = fields.DatetimeField(null=True, description="Timestamp of revocation")

    class Meta:
        table = "issued_certificate"

    def __str__(self):
        return f"SN: {self.serial_number} (CN: {self.request.common_name if self.request else 'N/A'}, Expires: {self.expires_at})"
