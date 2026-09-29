from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "SUPER_ADMIN"
        )


class IsCompanyAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                "SUPER_ADMIN",
                "COMPANY_ADMIN",
            ]
        )


class IsProcurementManager(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                "SUPER_ADMIN",
                "COMPANY_ADMIN",
                "PROCUREMENT_MANAGER",
            ]
        )


class IsEmployee(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                "SUPER_ADMIN",
                "COMPANY_ADMIN",
                "PROCUREMENT_MANAGER",
                "EMPLOYEE",
            ]
        )


class IsVendor(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "VENDOR"
        )


class IsAuthenticatedUser(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated