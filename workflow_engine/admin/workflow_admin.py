from django.contrib import admin


class WorkflowAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("workflow_engine/css/dagre.css", )
        }
        js = (
            'workflow_engine/javascript/cytoscape.min.js',
            'workflow_engine/javascript/workflow_graph.js',
        )

    change_list_template = 'admin/workflow_change_list.html'
    list_display = [
        'id',
        'name',
        'description',
        'disabled',
        'use_pbs',
        'archived'
        ]
    list_select_related = []
    list_filter = ['archived']
    actions = []
    inlines = []

    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        return response