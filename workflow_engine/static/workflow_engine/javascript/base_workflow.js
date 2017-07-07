function BaseWorkflow(milliseconds_between_refresh){
    ZERO = 0;
    ONE = 1;
    TWO = 2;
    ONE_HUNDRED = 100;
    TASK_SHOW_URL = '/workflow_engine/tasks/get_show_data';
    JOB_SHOW_URL = '/workflow_engine/jobs/get_show_data';
    JOB_QUEUE_SHOW_URL = '/workflow_engine/job_queues/get_show_data';
    QUEUE_JOB_URL = '/workflow_engine/jobs/queue_job';
    KILL_JOB_URL = '/workflow_engine/jobs/kill_job';
    QUEUE_TASK_URL = '/workflow_engine/tasks/queue_task';
    KILL_TASK_URL = '/workflow_engine/tasks/kill_task';
    TASK_STATUS_URL = '/workflow_engine/tasks/get_status';
    JOB_STATUS_URL = '/workflow_engine/jobs/get_status';
    DELETE_URL = '/workflow_engine/delete_record';
    UPDATE_URL = '/workflow_engine/update_record/';
    RECORD_INFO_URL = '/workflow_engine/get_record_info';
    CHECK_UNIQUE_URL = '/workflow_engine/check_unique';
    RUN_ALL_JOBS = '/workflow_engine/jobs/run_all';
    DOWNLOAD_BASH_URL = '/workflow_engine/tasks/download_bash';
    GET_EXECUTABLES_URL = '/workflow_engine/executables/get_names';
    GET_ENQUEUED_OBJECT_CLASSES_URL = '/workflow_engine/job_queues/get_enqueued_object_classses';
    GET_SEARCH_DATA_URL = '/workflow_engine/get_search_data';
    var search_criteria = {};
    var search_set = false;

    init(milliseconds_between_refresh);

    function get_search_data(search_type){
        var search_data = null;

        var url = GET_SEARCH_DATA_URL + '?search_type=' + search_type;
        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(data.success){
                search_data = data.payload;
            }
            else {
                alert('someting went wrong getting search data');
            }
        });

        return search_data;
    }

    function add_highlighting(text){
        if(text !== null){
            text = text.replace(/[^( |\)|\(|\n)]*(success)[^( |\)|\(|\n)]*/gi, '<span class = log_s>$1</span>')
            text = text.replace(/[^( |\)|\(|\n)]*(warnings)[^( |\)|\(|\n)]*/gi, '<span class = log_warn>$1</span>')
            text = text.replace(/[^( |\)|\(|\n|:)]*(errors)[^( |\)|\(|\n|:)]*/gi, '<span class = log_er>$1</span>')
            text = text.replace(/[^( |\)|\(|\n)]*(exception)[^( |\)|\(\n)]*/gi, '<span class = log_er>$1</span>')
            text = text.replace(/[^( |\)|\(|\n|:)]*(failure)[^( |\)|\(|\n|:)]*/gi, '<span class = log_er>$1</span>')
            text = text.replace(/[^( |\)|\(|\n|:)]*(fail)[^( |\)|\(|\n|:)]*/gi, '<span class = log_er>$1</span>')
        }

        return text;
    }

    function is_selected_option(selected, id, key){
        option_selected = '';

        if((id in search_criteria)  && (id in selected) && (key in selected[id])){
            option_selected = 'selected';
        }

        return option_selected;
    }

    function add_select_dropdown_html(records, name, id, selected){
        search_criteria[id] = true

        var html = '';
        html+='<tr>';
        html+='<th class="search">' +  name + '</th>';
        html+='<th class="search">';
        html+= '<select id="' + id + '" multiple="multiple">';
      
        for(key in records){

            var option_selected = is_selected_option(selected, id, key);
            html+= '<option ' + option_selected + '  value="' + key + '">'+ records[key] + '</option>';
        }

        html+='</select>';
        html+='</th>';
        html+='</tr>';

        return html;
    }

    function multiselect_init(id){

        $('#' + id).multiselect({
            maxHeight: "350",
            buttonWidth: '300px',
            enableCaseInsensitiveFiltering: true
        });
    }

    function get_first_page(url){
        //this gets the base url without the params and adds a /1/ to the end of it
        return url.replace(/(.*\/workflow_engine\/([a-z]|_)+)(\?|\&|$|\/[0-9]+)(.*)/, '$1/1/')
    }

    function get_selected_criteria(){
        var selected_criteria = {}
        for(search_id in search_criteria){    

            var first_time = true;
            $("#" + search_id).each(function(idx, tr) {
                var tr = $(tr);
                var selected = tr.find("option:selected");

                for(var j = ZERO; j < selected.length; j++){
                    var selection = selected[j].value;

                    var selected_values;
                    if(search_id in selected_criteria){
                        selected_values = selected_criteria[search_id];
                    }
                    else{
                        selected_values = [];
                    }

                    selected_values.push(selection);
                    selected_criteria[search_id] = selected_values;
                }
            });
        }

        return selected_criteria;
    }

    function set_url_with_criteria(url, selected_criteria){
        var first_time = true;
        for(criteria in selected_criteria){
            if(first_time){
                first_time = false;
                url += '?';
            }
            else{
                url += '&';
            }

            url+= criteria + '=' + selected_criteria[criteria].join(',');
        }

        return url;
    }

    function create_url(){
        var url = get_first_page(window.location.href);
        
        var selected_criteria = get_selected_criteria();
        url = set_url_with_criteria(url, selected_criteria);

        return url;
    }

    function set_job_queue_html(dialog){
        var search_data = get_search_data('job_queue');
        var ids = search_data['ids'];
        var names = search_data['names'];
        var job_strategy_classes = search_data['job_strategy_classes'];
        var enqueued_object_classes = search_data['enqueued_object_classes'];

        var selected = get_selected_search();

        var html = '<div><table>';

        html+= add_select_dropdown_html(ids, 'Id', 'job_queue_ids', selected);
        html+= add_select_dropdown_html(names, 'Name', 'job_queue_names', selected);
        html+= add_select_dropdown_html(job_strategy_classes, 'Job Strategy Class', 'job_strategy_classes', selected);
        html+= add_select_dropdown_html(enqueued_object_classes, 'Enqueued Object Classes', 'enqueued_object_classes', selected);

        html+= '</table></div>';

        dialog.append(html);

        multiselect_init('job_queue_ids');
        multiselect_init('job_queue_names');
        multiselect_init('job_strategy_classes');
        multiselect_init('enqueued_object_classes');
    }

    function set_tasks_html(dialog){
        var search_data = get_search_data('task');
        var ids = search_data['ids'];
        var enqueued_task_object_ids = search_data['enqueued_task_object_ids'];
        var enqueued_task_object_classes = search_data['enqueued_task_object_classes'];
        var job_ids = search_data['job_ids'];
        var run_state_ids = search_data['run_state_ids'];

        var selected = get_selected_search();

        var html = '<div><table>';
        
        html+= add_select_dropdown_html(ids, 'Id', 'task_ids', selected);
        html+= add_select_dropdown_html(enqueued_task_object_ids, 'Enqueued Task Object Id', 'enqueued_task_object_ids', selected);
        html+= add_select_dropdown_html(enqueued_task_object_classes, 'Enqueued Object Class', 'enqueued_task_object_classes', selected);
        html+= add_select_dropdown_html(job_ids, 'Job Id', 'job_ids', selected);
        html+= add_select_dropdown_html(run_state_ids, 'Run State', 'run_state_ids', selected);

        html+= '</table></div>';

        dialog.append(html);

        multiselect_init('task_ids');
        multiselect_init('enqueued_task_object_ids');
        multiselect_init('enqueued_task_object_classes');
        multiselect_init('job_ids');
        multiselect_init('run_state_ids');
    }

    function set_jobs_html(dialog){
        var search_data = get_search_data('job');
        var ids = search_data['ids'];
        var enqueued_object_ids = search_data['enqueued_object_ids'];
        var run_state_ids = search_data['run_state_ids'];
        var workflow_ids = search_data['workflow_ids'];

        var selected = get_selected_search();

        var html = '<div><table>';
        
        html+= add_select_dropdown_html(ids, 'Id', 'job_ids', selected);
        html+= add_select_dropdown_html(enqueued_object_ids, 'Enqueued Object Id', 'enqueued_object_ids', selected);
        html+= add_select_dropdown_html(run_state_ids, 'Run State', 'run_state_ids', selected);
        html+= add_select_dropdown_html(workflow_ids, 'Workflow', 'workflow_ids', selected);

        html+= '</table></div>';

        dialog.append(html);

        multiselect_init('job_ids');
        multiselect_init('enqueued_object_ids');
        multiselect_init('run_state_ids');
        multiselect_init('workflow_ids');
    }

    function get_selected_search(){
        var selected = {}
        var url = window.location.href

        url = url.replace(/(\?|\&)/g, ' ')

        var params = url.split(' ');
        
        for(var i = ZERO; i < params.length; i++){
            var param = params[i];

            var param_data = param.split('=');

            if(param_data.length === TWO){
                var selected_data = {}
                var name_key = param_data[ZERO];

                if(name_key !== ''){
                    var name_values = param_data[ONE].split(',');

                    for(var j = ZERO; j < name_values.length; j++){
                        selected_data[name_values[j]] =  true;
                    }

                    selected[name_key] = selected_data;
                }
            }
        }

        return selected;
    }

    function set_executable_html(dialog){
        var search_data = get_search_data('executable');
        var ids = search_data['ids'];
        var names = search_data['names'];
        var pbs_queues = search_data['pbs_queues'];
        var pbs_processors = search_data['pbs_processors'];
        var pbs_walltimes = search_data['pbs_walltimes'];

        var selected = get_selected_search();

        var html = '<div><table>';
        
        html+= add_select_dropdown_html(ids, 'Id', 'executable_ids', selected);
        html+= add_select_dropdown_html(names, 'Name', 'names', selected);
        html+= add_select_dropdown_html(pbs_queues, 'Pbs Queue', 'pbs_queues', selected);
        html+= add_select_dropdown_html(pbs_processors, 'Pbs Processor', 'pbs_processors', selected);
        html+= add_select_dropdown_html(pbs_walltimes, 'Pbs Walltime', 'pbs_walltimes', selected);

        html+= '</table></div>';

        dialog.append(html);

        multiselect_init('executable_ids');
        multiselect_init('names');
        multiselect_init('pbs_queues');
        multiselect_init('pbs_processors');
        multiselect_init('pbs_walltimes');
    }

    function set_search_html(dialog, type){
        dialog.empty();

        if(type == 'Executables'){
            set_executable_html(dialog);
        }
        else if(type == 'Job Queues'){
            set_job_queue_html(dialog);
        }

        else if(type == 'Jobs'){
            set_jobs_html(dialog);
        }

        else if(type == 'Tasks'){
            set_tasks_html(dialog);
        }
    }

    this.open_search_dialog = function(type){
        var dialog = $('#search_dialog');

        if(!search_set){
            search_set = true;
            set_search_html(dialog, type);
        }        

        if(!dialog.dialog("isOpen"))
        {     
            dialog.dialog( "open" );
        }          
    }

    this.set_search_dialog = function(type){
        var dialog = $('#search_dialog');

        var title = 'Search ' + type;

        $(function() {
            dialog.dialog({
                autoOpen: false,
                title: title,
                width:'auto',
                height:700,
                buttons: {
                    Search: function() {
                        window.location.replace(create_url())
                    }
                }
            });
        });      
    }

    function update_task_status(){
        var ids = get_task_ids_on_page();

        if(ids.length > ZERO){

            var url = TASK_STATUS_URL + '?task_ids=' + ids;

            var request = $.ajax({
                method: "GET",
                url: url,
                dataType: "JSON",
                async: false
            });

            //on success
            request.done(function (data) {
                if (data.success){

                    var payload = data.payload
                    for(var task_id in payload){
                        var job_data = payload[task_id];
                        var running_state = job_data['run_state_name'];
                        var start_run_time = job_data['start_run_time'];
                        var end_run_time = job_data['end_run_time'];
                        var duration = job_data['duration'];

                        var running_state_td = $('#job_state_' + task_id);

                        var old_running_state = running_state_td.html();

                        if(old_running_state !== running_state){

                            running_state_td.html(running_state);
                            running_state_td.removeClass(get_color_class(old_running_state)).addClass(get_color_class(running_state));

                            $('#duration_' + task_id).html(duration);
                            $('#start_run_time_' + task_id).html(start_run_time);
                            $('#end_run_time_' + task_id).html(end_run_time);

                            update_start_kill(task_id, running_state, 'task');
                        }
                    }
                }
            });
        }
    }

    this.create_new = function(type){
        this.update_record(type, 'new');
    }

    function null_to_empty(value){
        if(value === null){
            value = '';
        }

        return value;
    }

    function get_create_update_id(id, type, key){
        return (type + '_' + id + '_' + key)
    }

    function set_create_update_html(record_info, type, id, required_fields){
        var html = '<div id="update_create_' + id + '"><div class= "update_create_error_messages" id="update_create_error_messages_'+ id + '"></div>';
        html+= '<table>';

        var order_length = record_info.order_length;

        for(var index = 0; index < order_length; index++){
            var items = record_info[index];

            for(var key in items){
                html+='<tr>';
                
                var value = null_to_empty(items[key]);

                var required = '';
                if(key in required_fields){
                    required = '*';
                }

                html+='<th>' + key + required + '</th>'; 

                html+='<th><input id="' + get_create_update_id(id, type, key) + '" class="save_update save_update_'+ id + '" type="text" name="' + key + '" value="' + value + '"></th>';
                html+='</tr>';
            }
        }

        html+= '</table></div>';

        return html;
    }

    function get_record_info(type, id){
        var record_info = null;

        var url = RECORD_INFO_URL + '?record_type=' + type + '&record_id=' + id;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                record_info = data.payload
            }
            else{
                alert(data.message);
            }
        });

        return record_info
    }

    // function add_update_create_div(id){
    //     var html = '<div id="' + id + '"></div>';

    //     // $('#update_create').append(html);

    //     // return $("#" + id);
    //     return html;
    // }


    // function get_update_create_dialog_code(id){
    //     var html_id = 'update_create_' + id;
    //     // var dialog_code = $("#" + html_id);

    //     //create element if needed
    //     // if(element_exists(dialog_code)){
    //         // dialog_code.remove(); 
    //     // }

    //     dialog_code = add_update_create_div(html_id);

    //     return dialog_code;
    // }

    function save_update(id, type){
        var record_data = {};

        $('.save_update_' + id).each(function( index ) {
            var key = $(this).attr('name');
            var value = $(this).val();
            record_data[key] = value;
        });

        var url = UPDATE_URL + '?record_type=' + type + '&record_id=' + id;

        var request = $.ajax({
            type: "POST",
            url: url,
            async: false,
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify(record_data)
        });

        //on success
        request.done(function (data) {
            if (data.success){
                unique = data.payload
            }
            else{
                alert(data.message);
            }
        });

        return true
    }

    function is_integer(number){
        var value = Math.floor(Number(number));
        return String(value) === number;
    }

    function validate_range(id, type, field_name, min, max){
        var value_id = get_create_update_id(id, type, field_name);
        var valid = true;

        var item = $('#' + value_id);

        if(Number(item.val()) < min || Number(item.val()) > max){
            item.addClass('invalid_input')
            var error_message = field_name + ' must be between ' + min + ' and ' + max;
            var html = '<p>' + error_message + '</p>';
            $('#update_create_error_messages_'+ id).append(html);
            valid = false;
        }

        return valid;
    }

    function validate_integer(id, type, field_name){
        var value_id = get_create_update_id(id, type, field_name);
        var valid = true;

        var item = $('#' + value_id);

        if(!is_integer(item.val())){
            item.addClass('invalid_input')
            var error_message = field_name + ' must be an integer';
            var html = '<p>' + error_message + '</p>';
            $('#update_create_error_messages_'+ id).append(html);
            valid = false;
        }

        return valid;
    }

    function validate_not_null(id, type, field_name){
        var value_id = get_create_update_id(id, type, field_name);
        var valid = true;

        var item = $('#' + value_id);

        if(item.val().length === ZERO){
            item.addClass('invalid_input')
            var error_message = field_name + ' is a required field';
            var html = '<p>' + error_message + '</p>';
            $('#update_create_error_messages_'+ id).append(html);
            valid = false;
        }

        return valid;
    }

    function is_unique(id, type, value, field_name){
        var unique = false;

        var url = CHECK_UNIQUE_URL + '?record_type=' + type + '&record_id=' + id + '&value=' + value + '&field_name=' + field_name;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                unique = data.payload;
            }
            else{
                alert(data.message);
            }
        });

        return unique;
    }

    function validate_acceptable_field(id, type, field_name, acceptable_records){
        var value_id = get_create_update_id(id, type, field_name);
        var item = $('#' + value_id);
        var value = item.val();
        var valid = false;

        for(var i = ZERO; !valid && i < acceptable_records.length; i++){
            if(value === acceptable_records[i]){
                valid = true;
            }
        }

        if(!valid){
            item.addClass('invalid_input')
            var error_message = value + ' is not a valid option for ' + field_name;
            var html = '<p>' + error_message + '</p>';
            $('#update_create_error_messages_'+ id).append(html);
        }

        return valid;
    }

    function validate_unique(id, type, field_name){
        var value_id = get_create_update_id(id, type, field_name);
        var valid = true;

        var item = $('#' + value_id);

        if(!is_unique(id, type, item.val(), field_name)){
            item.addClass('invalid_input')
            var error_message = field_name + ' must be unique';
            var html = '<p>' + error_message + '</p>';
            $('#update_create_error_messages_'+ id).append(html);
            valid = false;
        }

        return valid;
    }

    function validate_save(id, type){
        var valid = true;

        //clear old messages
        $('#update_create_error_messages_'+ id).empty()
        $('.save_update').removeClass('invalid_input')

        if(type == 'executable'){
            valid = validate_not_null(id, type, 'name') && valid;
            valid = validate_not_null(id, type, 'executable_path') && valid
            valid = validate_not_null(id, type, 'pbs_processor') && valid
            valid = validate_not_null(id, type, 'pbs_walltime') && valid
            valid = validate_not_null(id, type, 'pbs_queue') && valid
            valid = validate_unique(id, type, 'name') && valid;
        }
        else if(type == 'job_queue'){
            valid = validate_not_null(id, type, 'name') && valid;
            valid = validate_not_null(id, type, 'job_strategy_class') && valid
            valid = validate_not_null(id, type, 'enqueued_object_class') && valid
            valid = validate_unique(id, type, 'name') && valid;
            var executables = get_executables();
            executables.push('');
            valid = validate_acceptable_field(id, type, 'executable', executables) && valid
            valid = validate_acceptable_field(id, type, 'enqueued_object_class', get_enqueued_object_classses()) && valid

        }
        else if(id = 'new' && type == 'job'){
            // valid = validate_not_null(id, type, 'workflow_node_id') && valid;
            // valid = validate_not_null(id, type, 'enqueued_object_id') && valid;
        }
        else if(type == 'job'){
            valid = validate_not_null(id, type, 'priority') && valid;
            valid = validate_integer(id, type, 'priority') && valid;
            valid = validate_range(id, type, 'priority', ZERO, ONE_HUNDRED) && valid;
        }

        return valid;
    }

    function get_required_fields(type, id){
        var required_fields = {};
        if(type == 'executable'){
            required_fields['name'] = true; 
            required_fields['executable_path'] = true; 
            required_fields['pbs_processor'] = true; 
            required_fields['pbs_queue'] = true; 
            required_fields['pbs_walltime'] = true; 
        }
        else if(type == 'job_queue'){
            required_fields['name'] = true; 
            required_fields['job_strategy_class'] = true; 
            required_fields['enqueued_object_class'] = true; 
        }

        else if(type == 'job'){
            if(id == 'new'){
                required_fields['workflow_node_id'] = true; 
                required_fields['enqueued_object_id'] = true; 
            }
            else{
                required_fields['priority'] = true; 
            }
        }

        return required_fields;
    }

    this.download_bash = function(){
        var ids = get_task_ids_on_page();

        if(ids.length > ZERO){

            var url = DOWNLOAD_BASH_URL + '?task_ids=' + ids;

            var request = $.ajax({
                method: "GET",
                url: url,
                dataType: "JSON",
                async: false
            });

            //on success
            request.done(function (data) {
                if (data.success){
                    var payload = data.payload;
                    var error_message = data.error_message;
                    if(error_message.length > ZERO){
                        alert('Errors generating bash file: ' + error_message.join(','));
                    }

                    var content = '#!/bin/bash\n';
                    for(var i = 0; i < payload.length; i++){
                        var command = payload[i];
                        content+= command + '\n';
                    }

                    var element = document.createElement('a');
                    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
                    element.setAttribute('download', 'run.sh');

                    element.style.display = 'none';
                    document.body.appendChild(element);
                    element.click();

                    document.body.removeChild(element);

                }
                else{
                    alert('something went wrong')
                }
            });
        }
    }

    this.run_all_jobs = function(){

        var ids = get_job_ids_on_page();
        if(ids.length > 0){

            var url = RUN_ALL_JOBS + '?job_ids=' + ids.join(',');

            var request = $.ajax({
                method: "GET",
                url: url,
                dataType: "JSON",
                async: false
            });

            //on success
            request.done(function (data) {
                if (data.success){
                    update_job_status();
                }
                else{
                    alert('someting went wrong running all')
                }
            });
        }
    }

    function get_enqueued_object_classses(){
        var enqueued_object_classses = [];
        var url = GET_ENQUEUED_OBJECT_CLASSES_URL;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                enqueued_object_classses = data.payload
            }
            else{
                alert('someting went wrong loading enqueued object classes')
            }
        });

        return enqueued_object_classses;
    }

    function get_executables(){

        var executables = [];
        var url = GET_EXECUTABLES_URL;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                executables = data.payload
            }
            else{
                alert('someting went wrong loading executables')
            }
        });

        return executables;
    }

    function show_auto_complete(id){
        $("#" + id).trigger( "focus" );
        $("#" + id).autocomplete("search", "");
    }

    function show_auto_complete_event(event){
        $("#" + event.data.id).trigger( "focus" );
        $("#" + event.data.id).autocomplete("search", "");
    }

    function add_enqueued_object_class_lookahead(id, type){
        var enqueued_object_class_id = get_create_update_id(id, type, 'enqueued_object_class')
        var enqueued_object_classses = get_enqueued_object_classses();

        var input = $('#' + enqueued_object_class_id);

        input.autocomplete({
            source: enqueued_object_classses,
            minLength:0
        });

        // show_auto_complete(executable_id);
        input.click({id: enqueued_object_class_id}, show_auto_complete_event);
    }

    function add_executable_lookahead(id, type){
        var executable_id = get_create_update_id(id, type, 'executable')
        var executables = get_executables();
        var executable_input = $('#' + executable_id);

        executable_input.autocomplete({
            source: executables,
            minLength:0
        });

        // show_auto_complete(executable_id);
        executable_input.click({id: executable_id}, show_auto_complete_event);
    }

    this.update_record = function(type, id){
        var html_id = 'update_create_' + id;
        var dialog = $("#" + html_id);

        if(dialog.length !== ZERO){
            if(!dialog.dialog("isOpen")){
                dialog.dialog("open");
            }
        }

        else{
            var record_info = get_record_info(type, id)

            if(record_info !== null){
                var required_fields = get_required_fields(type, id);
                var html = set_create_update_html(record_info, type, id, required_fields);

                var title = 'Update ' + type + ' ' + id;

                if(id === 'new'){
                    title = 'Create new ' + type;
                }

                $(function() {
                    $(html).dialog({
                        title: title,
                        width:'auto',
                        height:'auto',
                        create: function(){
                            if(type === 'job_queue'){
                                add_executable_lookahead(id, type);
                                add_enqueued_object_class_lookahead(id, type);
                            }
                        },
                        buttons: {
                          Save: function() {
                            var valid = validate_save(id, type);
                            if(valid){
                                var success = save_update(id, type);
                                if(success){
                                    $(this).dialog("close");
                                    location.reload(); 
                                }
                            }
                          }
                        }
                    });
                } );     

                
            }
        }
    }

    this.delete_record = function(type, id){

        if(type === 'executable' || type === 'job_queue' || type === 'job'){
            if(confirm("Are you sure you wish to delete this record?")){

                var url = DELETE_URL + '?record_type=' + type + '&record_id=' + id;

                var request = $.ajax({
                    method: "GET",
                    url: url,
                    dataType: "JSON",
                    async: false
                });

                //on success
                request.done(function (data) {
                    if (data.success){
                        location.reload(); 
                    }
                    else{
                        var dialog = $('#delete_dialog');
                        if(dialog.length !== ZERO)
                        {
                           if(!dialog.dialog("isOpen")){
                                dialog.dialog("open");
                            } 
                        }
                        else{

                            var title = 'Could not delete';

                            var content = data.message;
                            var link_content = data.link_content;
                            var link = data.link;

                            var html = add_delete_content(content, link_content, link);

                            // alert(data.message)
                            $(function() {
                                $(html).dialog({
                                    title: title,
                                    width:'auto',
                                    height:'auto',
                                    buttons: {
                                      Ok: function() {
                                        $(this).dialog( "close" );
                                      }
                                    }
                                });
                            });
                        }
                    }
                });
            }
        }
        else{
            alert('type: ' + type + ' not supported for delete')
        }
    }

    function get_task_ids_on_page(){
        var ids = [];
        $('.class_task_id').each(function() {
            ids.push(this.id)
        });

        return ids
    }

    function get_job_ids_on_page(){
        var ids = [];
        $('.class_job_id').each(function() {
            ids.push(this.id)
        });

        return ids
    }

    function get_color_class(run_state_name){
        var color = 'color_' + run_state_name.toLowerCase()

        return color
    }

    function update_job_status(){
        var ids = get_job_ids_on_page();
        if(ids.length > 0){

            var url = JOB_STATUS_URL + '?job_ids=' + ids.join(',');

            var request = $.ajax({
                method: "GET",
                url: url,
                dataType: "JSON",
                async: false
            });

            //on success
            request.done(function (data) {
                if (data.success){
                    var payload = data.payload
                    for(var job_id in payload){
                        var task_data = payload[job_id];

                        var running_state = task_data['run_state_name'];
                        var start_run_time = task_data['start_run_time'];
                        var end_run_time = task_data['end_run_time'];
                        var duration = task_data['duration'];

                        var running_state_td = $('#job_state_' + job_id);

                        var old_running_state = running_state_td.html();

                        if(old_running_state !== running_state){

                            running_state_td.html(running_state);
                            running_state_td.removeClass(get_color_class(old_running_state)).addClass(get_color_class(running_state));

                            $('#duration_' + job_id).html(duration);
                            $('#start_run_time_' + job_id).html(start_run_time);
                            $('#end_run_time_' + job_id).html(end_run_time);

                            update_start_kill(job_id, running_state, 'job');
                        }
                    }
                }
            });
        }
    }

    function update_start_kill(id, run_state_name, type){
        var row = $('#run_option_' + id);
        row.empty();

        var html = '';

        if(run_state_name == 'PENDING' || run_state_name == 'FAILED' || run_state_name == 'SUCCESS' || run_state_name == 'PROCESS_KILLED' || run_state_name == 'FAILED_EXECUTION'){
            html+= "<img onclick='base_workflow.queue_" + type + "(" + id + ")' src='/static/workflow_engine/images/run.png' alt='Run'/>";
        }
        else{
            html+= "<img onclick='base_workflow.kill_" + type + "(" + id + ")' src='/static/workflow_engine/images/kill.png' alt='Kill'/>";
        }
        row.append(html);
    }

    function update_status(){
        update_task_status();
        update_job_status();
    }

    function make_ajax_call(url){
        var content = [];

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                var payload = data.payload
                var order_length = payload.order_length;

                for(var index = 0; index < order_length; index++){
                    var items = payload[index];

                    for(var key in items){
                        var content_item = new Object();
                        content_item.key = key;
                        content_item.value = items[key];
                        content.push(content_item);
                    }
                }
            }
            else{
                alert('Something went wrong loading show data: ' + data.message)
            }
        });

        return content;
    }

    this.queue_task = function(id){
        var url = QUEUE_TASK_URL + '?task_id=' + id

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                update_status();
            }
            else{
                alert('Something went wrong starting task: ' + data.message)
            }
        });
    }

    this.kill_task = function(id){
        var url = KILL_TASK_URL + '?task_id=' + id

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                update_status();
            }
            else{
                alert('Something went wrong killing task: ' + data.message)
            }
        });
    }

    this.kill_job = function(id){
        var url = KILL_JOB_URL + '?job_id=' + id

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                update_status();
            }
            else{
                alert('Something went wrong killing job: ' + data.message)
            }
        });
    }

    this.queue_job = function(id){
        var url = QUEUE_JOB_URL + '?job_id=' + id

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (data.success){
                update_status();
            }
            else{
                alert('Something went wrong starting job: ' + data.message)
            }
        });
    }

    function get_show_content(action, id){
        var content = [];

        if(action === 'task'){
            var url = TASK_SHOW_URL + '?task_id=' + id
            content = make_ajax_call(url);
        }
        else if(action == 'job_queue'){
            var url = JOB_QUEUE_SHOW_URL + '?job_queue_id=' + id
            content = make_ajax_call(url);
        }
        else if(action == 'job'){
            var url = JOB_SHOW_URL + '?job_id=' + id
            content = make_ajax_call(url);
        }
        else{
            alert('show action: ' + action + ' not supported yet')
        }

        return content;
    }

    function element_exists(element){
        return (element.length > ZERO);
    }

    function add_delete_content(content, link_content, link){
        return "<div id='delete_dialog'><p>" + content + "<span><a class='link_to_page' href='" + link + "'>" + link_content + "</a></span></p></div>";
    }

    function add_show_content(content, action, id){
        var html = '<div id="show_content_' + id + '">';
        for(var index = ZERO; index < content.length; index++){
            var item = content[index];

            if(item.key == 'error message'){
                item.value = add_highlighting(item.value); 
            }

            if(action === 'task' && item.key == 'full executable'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/logs?types=executable&task_id='+ id + '">' + item.value  + "</a></div>";
            }

            else if(action === 'task' && item.key == 'log file'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/logs?types=log&task_id='+ id + '">' + item.value  + "</a></div>";
            }

            else if(action === 'task' && item.key == 'input file'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/logs?types=input_file&task_id='+ id + '">' + item.value  + "</a></div>";
            }

            else if(action === 'task' && item.key == 'output file'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/logs?types=output_file&task_id='+ id + '">' + item.value  + "</a></div>";
            }

            else if(action === 'task' && item.key == 'pbs file'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/logs?types=pbs&task_id='+ id + '">' + item.value  + "</a></div>";
            }

            else if(action === 'job_queue' && item.key == 'executable path'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/logs?job_queue_id='+ id + '">' + item.value  + "</a></div>";
            }

            else if(action === 'job' && item.key == 'workflow'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/workflows?workflow_names='+ item.value + '">' + item.value  + "</a></div>";
            }

            else if(action === 'job' && item.key == 'job queue'){
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span><a class="link_to_page show_link" href="/workflow_engine/job_queues?job_queue_names='+ item.value + '">' + item.value  + "</a></div>";
            }

            else{
                html+="<div class='show_rows'><span class='content_key'>" + item.key + ': </span>' + item.value  + "</div>";
            }
        }

        html+='</div>';

        return html;
    }

    this.set_show_dialog = function(page, action, id){
  
        var title = page + ' ' + id;
        var content = get_show_content(action, id);

        var html_id = 'show_content_' + id;
        var dialog = $("#" + html_id);

        if(dialog.length !== ZERO){
            if(!dialog.dialog("isOpen")){
                dialog.dialog("open");
            }
        }
        else{
            var html = add_show_content(content, action, id);

            $(function() {
              $(html).dialog({
                title: title,
                width:'auto',
                height:'auto',
                buttons: {
                  Ok: function() {
                    $( this ).dialog( "close" );
                  }
                }
              });
            });
        }
    }

    function init(milliseconds_between_refresh) {
        window.setInterval(update_status, milliseconds_between_refresh);
    }
}