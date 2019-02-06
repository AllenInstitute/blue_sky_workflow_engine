from django.contrib import admin


class WorkflowEdgeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'source',
        'sink',
        'disabled',
        'archived'
        ]
    read_only_fields = (
        )
    list_select_related = (
        )
    list_filter = [
        'workflow',
        'disabled',
        'archived']
    actions = []
