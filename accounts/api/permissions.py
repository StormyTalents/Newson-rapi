from rest_framework import permissions


class MustBeAppSumoUserPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.userprofile.app_sumo_user