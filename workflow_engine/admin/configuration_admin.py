from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'attachable_link',
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


    def attachable_link(self, configuration_object):
        attachable_object = configuration_object.content_object
        clz = attachable_object._meta.db_table
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:{}_change".format(clz),
                    args=(attachable_object.id,)),
            str(attachable_object)))

    attachable_link.short_description = "Attached Object"
