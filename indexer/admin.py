from django.contrib import admin
from django.contrib.auth.models import Group, User

from indexer.models import Author, Repository

# remove the models from admin interface
admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("company", "team", "real_name", "real_email", "name", "email")
    search_fields = ["real_name", "real_email", "name", "email"]
    ordering = ["company", "team", "real_email"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("repo_group", "component", "repo_name", "is_active", "clone_url")
    search_fields = ["repo_group", "component", "repo_name"]
    ordering = ["repo_group", "component", "repo_name"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
