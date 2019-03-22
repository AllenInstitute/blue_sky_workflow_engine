from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe


class WellKnownFileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'attachable_link',
        'record_dir',
        'record_filename',
        'well_known_file_type',
        'created_at',
        'updated_at'
        )
    read_only_fields = (
        'record_dir',
        'record_filename',
        'created_at',
        'updated_at'
        )
    list_select_related = []
    list_filter = [
        'attachable_type',
        'well_known_file_type'
    ]

    def record_dir(self, wkf_object):
        try:
            rd = str(wkf_object.get_most_recent_file_record().storage_directory)
        except:
            rd = '-'

        return rd

    def record_filename(self, wkf_object):
        try:
            rfn = str(wkf_object.get_most_recent_file_record().filename)
        except:
            rfn = '-'

        return rfn

    def attachable_link(self, well_known_file_object):
        attachable_object = well_known_file_object.content_object
        clz = attachable_object._meta.db_table
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:{}_change".format(clz),
                    args=(attachable_object.id,)),
            str(attachable_object)))

    attachable_link.short_description = "Attached Object"