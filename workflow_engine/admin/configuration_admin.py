from django.contrib import admin


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'content_type',
        'object_id',
        'name',
        'configuration_type',
        'created_at',
        'updated_at'
        )
    read_only_fields = (
        'created_at',
        'updated_at'
        )
    list_select_related = []
    list_filter = [
        'content_type',
        'configuration_type'
    ]
