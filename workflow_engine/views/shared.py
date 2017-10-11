# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the
# Allen Institute's written permission.
# For purposes of this license, commercial purposes is the incorporation of the
# Allen Institute's software into anything for which you will charge fees or
# other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
from django.core.paginator import Paginator
from workflow_engine.models import *
from django.conf import settings
import workflow_engine
import re

def add_settings_info_to_context(context):
    context['milliseconds_between_refresh'] = settings.MILLISECONDS_BETWEEN_REFRESH
    # context['csrf_token'] = settings.MILLISECONDS_BETWEEN_REFRESH
    context['workflow_version'] = workflow_engine.__version__

def to_none(value):
    result = value

    if result == '':
        result = None
    return result

def set_order(payload, order, key, value):
    payload[order] = {key: value}
    order+=ONE
    return order

def string_to_bool(input):
    return input.lower() == 'true'

def sort_helper(column_name, sort, url, set_params):
    #take off the old sort params
    url = re.sub(r"(&|\?)sort=.*", '', url, flags=re.IGNORECASE)

    if sort == column_name or sort == ('-' + column_name):
        if(sort[:ONE] == '-'):
            #remove the first char
            result = sort[ONE:]
        else:
            #add the '-'
            result = '-' + sort
    else:
        result = '-' + column_name

    if set_params:
        result = url + '&sort=' + result
    else:
        result = url + '?sort=' + result
 
    return result

def get_page_range_start(page_range_end):
    result = page_range_end + ONE - settings.MAX_DISPLAYED_PAGE_LINKS

    #min is one
    if result < ONE:
        result = ONE

    return result

def get_page_range_end(num_pages, page):
    result = page + int(settings.MAX_DISPLAYED_PAGE_LINKS / TWO)

    if result < settings.MAX_DISPLAYED_PAGE_LINKS:
        result = settings.MAX_DISPLAYED_PAGE_LINKS

    if result >= num_pages:
        result = num_pages

    return result

def page_link_helper(url, selected_page, page_number):
    #replace the pagenumber
    return re.sub(str(selected_page) + '/([0-9]+)/', str(selected_page) + '/' + str(page_number) + '/', url, flags=re.IGNORECASE)

def add_context(context, records, page_link, page, selected_page):
    page = int(page)

    paginator = Paginator(records, settings.RESULTS_PER_PAGE)

    if page > paginator.num_pages:
        page = paginator.num_pages

    paginator_records = paginator.page(page)

    context['selected_page'] = selected_page
    context['records'] = paginator_records
    context['page'] = page
    context['number_of_pages'] = paginator.num_pages
    context['number_of_records'] = len(records)
    context['page_range_end'] = get_page_range_end(paginator.num_pages, page)
    context['page_range_start'] = get_page_range_start(context['page_range_end'])
    context['full_end'] = paginator.num_pages
    context['full_end_link'] = page_link_helper(page_link, selected_page, context['full_end'])
    context['full_start'] = ONE
    context['full_start_link'] = page_link_helper(page_link, selected_page, context['full_start'])

    context['page_range'] = range(context['page_range_start'], context['page_range_end'] + ONE)
    context['has_next'] = paginator_records.has_next()
    context['has_previous'] = paginator_records.has_previous()
    context['display_start_link'] = (context['has_previous'] and context['page_range_start'] > ONE)
    context['display_end_link'] = (context['has_next'] and context['page_range_end'] != paginator.num_pages)


    page_links = []
    for page_number in context['page_range']:
        link_data = {}
        link_data['value'] = page_number
        link_data['link'] = page_link_helper(page_link, selected_page, page_number)
        page_links.append(link_data)

    context['page_links'] = page_links

    context['page_link'] = page_link

    if paginator_records.has_next():
        context['next_page'] = paginator_records.next_page_number()
        context['next_page_link'] = page_link_helper(page_link, selected_page, context['next_page'])

    if paginator_records.has_previous():
        context['previous_page'] = paginator_records.previous_page_number()
        context['previous_page_link'] = page_link_helper(page_link, selected_page, context['previous_page'])
