from django.contrib import admin


class WorkflowAdmin(admin.ModelAdmin):
    change_list_template = 'admin/workflow_change_list.html'
    list_display = [
        'id',
        'name',
        'description',
        'disabled',
        'use_pbs',
        ]
    list_select_related = []
    list_filter = []
    actions = []
    inlines = []

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        return response