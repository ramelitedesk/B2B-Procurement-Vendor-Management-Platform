from .models import AuditLog


def create_audit_log(
    *,
    user=None,
    company=None,
    action,
    description,
    object_type=None,
    object_id=None,
    previous_status=None,
    new_status=None,
    ip_address=None,
):
    return AuditLog.create_log(
        user=user,
        company=company,
        action=action,
        description=description,
        object_type=object_type,
        object_id=object_id,
        previous_status=previous_status,
        new_status=new_status,
        ip_address=ip_address,
    )