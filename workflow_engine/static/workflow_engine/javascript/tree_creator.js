function TreeCreator(workflows, milliseconds_between_refresh){
    UPDATE_PBS = '/workflow_engine/workflows/update_pbs';
    GET_ENQUEUED_OBJECTS_URL = '/workflow_engine/workflows/get_enqueued_objects';
    GET_HEAD_WORKFLOW_NODE_URL = '/workflow_engine/workflows/get_head_workflow_node_id';
    CREATE_JOB_URL = '/workflow_engine/workflows/create_job';
    GET_WORKFLOW_NODE_INFO_URL = '/workflow_engine/workflows/get_node_info';
    GET_WORKFLOW_INFO_URL = '/workflow_engine/workflows/get_workflow_info';
    UPDATE_WORKFLOW_NODE_URL = '/workflow_engine/workflows/update_workflow_node';
    CHECK_UNIQUE_URL = '/workflow_engine/check_unique';
    UPDATE_WORKFLOW_URL = '/workflow_engine/workflows/update_workflow';
    GET_SEARCH_DATA_URL = '/workflow_engine/get_search_data';
    WORKFLOW_STATUS_URL = '/workflow_engine/workflows/get_workflow_status';
    var search_criteria = {};
    var search_set = false;

    ZERO = 0;
    ONE_HUNDRED = 100;
    ONE_HUNDRED_THOUSAND = 100000;

    init(workflows, milliseconds_between_refresh);

    this.update_pbs = function(id, workflow_id){
        var use_pbs = $('#' + id).is(":checked");
        var url = UPDATE_PBS + '?workflow_id=' + workflow_id + '&use_pbs=' + use_pbs;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if (!data.success){
                alert('someting went wrong updating pbs - ' + data.message)
            }
        });
    }

    function create_tree(workflow){
        var my_chart = new Treant(workflow, $);
    }

    function create_workflow_node_job(event){
        event.preventDefault();
        var workflow_node_id = event.data.workflow_node_id;
        var workflow_id = event.data.workflow_id;
        create_job(workflow_node_id, workflow_id)
    }

    this.create_job_helper = function(workflow_node_id, workflow_id){
        create_job(workflow_node_id, workflow_id)
    }

    function update_workflow(workflow_id, type){
        var valid = true;

        var name = $('#' + get_create_update_id(workflow_id, type, 'name')).val();
        var description = $('#' + get_create_update_id(workflow_id, type, 'description')).val();
        var disabled = $('#' + get_create_update_id(workflow_id, type, 'disabled')).prop('checked');

        var url = UPDATE_WORKFLOW_URL + '?workflow_id=' + workflow_id + '&name=' + name + '&description=' + description + '&disabled=' + disabled;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(!data.success){
                alert('someting went wrong updating workflow');
            }
        });

        return true;

    }

    function update_workflow_node(workflow_node_id, type){

        var valid = true;

        var disabled = $('#' + get_create_update_id(workflow_node_id, type, 'disabled')).prop('checked');
        var overwrite = $('#' + get_create_update_id(workflow_node_id, type, 'overwrite')).prop('checked');
        var max_retries = $('#' + get_create_update_id(workflow_node_id, type, 'max_retries')).val();
        var batch_size = $('#' + get_create_update_id(workflow_node_id, type, 'batch_size')).val();
        var priority = $('#' + get_create_update_id(workflow_node_id, type, 'priority')).val();

        var url = UPDATE_WORKFLOW_NODE_URL + '?workflow_node_id=' + workflow_node_id + '&disabled=' + disabled + '&overwrite=' + overwrite + '&max_retries=' + max_retries + '&batch_size=' + batch_size + '&priority=' + priority;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(!data.success){
                alert('someting went wrong updating workflow node');
            }
        });

        return true;
    }

    function show_workflow_dialog(event){
        var workflow_id = event.data.workflow_id; 

        var html_id = 'workflow_dialog_' + workflow_id;
        var dialog = $("#" + html_id);

        if(dialog.length !== ZERO){
            if(!dialog.dialog("isOpen")){
                dialog.dialog("open");
            }
        }
        else{
            var html = set_workflow_html(workflow_id);

            var title = 'Update Workflow';
            var type = 'workflow_show';

            $(function() {
                $(html).dialog({
                    title: title,
                    width:'auto',
                    height:'auto',
                    buttons: {
                        Save: function() {
                            var valid = validate_save(workflow_id, type, []);
                            if(valid){
                                var success = update_workflow(workflow_id, type);
                                if(success){
                                    $(this).dialog("close");
                                    location.reload(); 
                                }
                            }
                        }
                    }
                });
            });     
        }  
    }

    function show_node_dialog(event){
        var workflow_node_id = event.data.workflow_node_id;
        var workflow_id = event.data.workflow_id; 

        var html_id = 'node_dialog_' + workflow_node_id;
        var dialog = $("#" + html_id);

        if(dialog.length !== ZERO){
            if(!dialog.dialog("isOpen")){
                dialog.dialog("open");
            }
        }
        else{
            var html = set_workflow_node_html(workflow_node_id, workflow_id)

            var title = 'Workflow Node Information';
            var type = 'workflow_node_show';

            $(function() {
                $(html).dialog({
                    title: title,
                    width:'auto',
                    height:'auto',
                    buttons: {
                        Save: function() {
                            var valid = validate_save(workflow_node_id, type, []);
                            if(valid){
                                var success = update_workflow_node(workflow_node_id, type);
                                if(success){
                                    $(this).dialog("close");
                                    location.reload(); 
                                }
                            }
                        }
                    }
                });
            });       
        }
    }

    function set_workflow_html(workflow_id){
        var html = '<div class="workflow_dialog_' + workflow_id + '"><div class= "create_job_error_messages" id="create_job_error_messages_'+ workflow_id + '"></div>';

        var url = GET_WORKFLOW_INFO_URL + '?workflow_id=' + workflow_id;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(data.success){
                payload = data.payload

                var name = payload['name'];
                var description = payload['description'];
                var disabled = payload['disabled'];

                var disabled_checked = '';

                if(disabled){
                    disabled_checked = 'checked';
                }

                html+= '<table>';
                html+='<tr><th>Name</th><th><input class="save_update_workflow" id="workflow_show_' + workflow_id + '_name" maxlength="255" size="100" value="' + name + '"></th></th></tr>';
                html+='<tr><th>Description</th><th><input class="save_update_workflow" maxlength="255" size="100" id="workflow_show_' + workflow_id + '_description" value="' + description + '"></th></tr>';
                html+='<tr><th>Disabled</th><th><input class="save_update_workflow" id="workflow_show_' + workflow_id + '_disabled" type="checkbox" value="disabled" ' + disabled_checked + '></th></tr>';
                html+= '</table>';

            }
            else {
                alert('someting went wrong getting node data - ' + data.message)
            }
        });

        html += '</div>';

        return html;
    }

    function set_workflow_node_html(workflow_node_id, workflow_id){
        var html = '<div id="node_dialog_' + workflow_node_id + '"><div class= "create_job_error_messages" id="create_job_error_messages_'+ workflow_node_id + '"></div>';

        var url = GET_WORKFLOW_NODE_INFO_URL + '?workflow_node_id=' + workflow_node_id;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(data.success){
                payload = data.payload

                var disabled = payload['disabled'];
                var overwrite_previous_job = payload['overwrite_previous_job'];
                var max_retries = payload['max_retries'];
                var batch_size = payload['batch_size'];
                var priority = payload['priority'];

                var disabled_checked = '';
                var overwrite_previous_job_checked = '';

                if(disabled){
                    disabled_checked = 'checked';
                }

                if(overwrite_previous_job){
                    overwrite_previous_job_checked = 'checked';
                }

                html+= '<table id="w_table">';
                html+='<tr><th class="show_link w_th" colspan="2" onclick="base_workflow.create_job_helper(' + workflow_node_id + ',' + workflow_id + ')">Create Job</th></tr>';
                html+='<tr><th class="w_th">ID</th><th class="w_th">' + workflow_node_id + '</th></tr>';
                html+='<tr><th class="w_th">Job Queue</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['job_queue_link'] + '">' + payload['job_queue'] + '</a></th></tr>';
                html+='<tr><th class="w_th">Executable</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['executable_link'] + '">' + payload['executable'] + '</a></th></tr>';
                html+='<tr><th class="w_th">Enqueued Object Class</th><th class="w_th">' + payload['enqueued_object_class'] + '</th></tr>';
                html+='<tr><th class="w_th">Number of Jobs</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['number_of_jobs_link'] + '">(' + payload['number_of_jobs'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">PENDING</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['pending_link'] + '">('  + payload['pending'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">QUEUED</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['queued_link'] + '">(' + payload['queued'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">RUNNING</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['running_link'] + '">(' + payload['running'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">FINISHED_EXECUTION</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['finished_execution_link'] + '">(' + payload['finished_execution'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">FAILED_EXECUTION</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['failed_execution_link'] + '">(' + payload['failed_execution'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">FAILED</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['failed_link'] + '">(' + payload['failed'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">SUCCESS</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['success_count_link'] + '">(' + payload['success_count'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">PROCESS_KILLED</th><th class="w_th"><a class="link_to_page show_link" href="' + payload['process_killed_link'] + '">(' + payload['process_killed'] + ')</a></th></tr>';
                html+='<tr><th class="w_th">Disabled</th><th class="w_th"><input class="save_update_node" id="workflow_node_show_' + workflow_node_id + '_disabled" type="checkbox" value="disabled" ' + disabled_checked + '></th></tr>';
                html+='<tr><th class="w_th">Overwrite Previous Job</th><th class="w_th"><input class="save_update_node" id="workflow_node_show_' + workflow_node_id + '_overwrite" type="checkbox" value="overwrite" ' + overwrite_previous_job_checked + '></th></tr>';
                html+='<tr><th class="w_th">Max Retries</th><th class="w_th"><input class="save_update_node" id="workflow_node_show_' + workflow_node_id + '_max_retries" class="max_retry_input" maxlength="4" size="4" type="text" value="' + max_retries + '"></th></tr>';
                html+='<tr><th class="w_th">Batch Size</th><th class="w_th"><input class="save_update_node" id="workflow_node_show_' + workflow_node_id + '_batch_size" class="batch_size" maxlength="4" size="4" type="text" value="' + batch_size + '"></th></tr>';
                html+='<tr><th class="w_th">Priority</th><th class="w_th"><input class="save_update_node" id="workflow_node_show_' + workflow_node_id + '_priority" class="batch_size" maxlength="4" size="4" type="text" value="' + priority + '"></th></tr>';
                html+= '</table>';

            }
            else {
                alert('someting went wrong getting node data - ' + data.message)
            }
        });

        html+= 'div';

        return html;
    }

    function set_show_node_dialog_click_handlers(){
        $(".workflow_node").each(function() {
            var workflow_id = $(this).attr('workflow_id');
            var workflow_node_id = $(this).attr('node_id');
            $(this).click({workflow_node_id: workflow_node_id, workflow_id: workflow_id}, show_node_dialog);
        });
    }

    function set_workflow_dialog_click_handlers(){
        $(".workflow_update").each(function() {
            var workflow_id = $(this).attr('workflow_id');
            $(this).click({workflow_id: workflow_id}, show_workflow_dialog);
        });
    }

    this.create_workflow_job = function(workflow_id){
        workflow_node_id = get_head_workflow_node_id(workflow_id);
        create_job(workflow_node_id, workflow_id);
    }  

    this.open_search_dialog = function(){
        var dialog = $('#search_dialog');

        if(!search_set){
            search_set = true;
            set_search_html(dialog);
        }        

        if(!dialog.dialog("isOpen"))
        {     
            dialog.dialog( "open" );
        }          
    }

    this.set_search_dialog = function(){
        var dialog = $("#search_dialog");
        var title = 'Search Workflows';

        $(function() {
            dialog.dialog({
                autoOpen: false,
                title: title,
                width:'auto',
                height:500,
                buttons: {
                    Search: function() {
                        window.location.replace(create_url())
                    }
                }
            });
        });    
    }

    function get_head_workflow_node_id(workflow_id){
        var workflow_node_id = null;

        var url = GET_HEAD_WORKFLOW_NODE_URL + '?workflow_id=' + workflow_id;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(data.success){
                workflow_node_id = data.payload
            }
            else {
                alert('someting went wrong getting head workflow node - ' + data.message)
            }
        });

        return workflow_node_id
    }

    function get_workflow_search_data(){
        var search_data = null;

        var url = GET_SEARCH_DATA_URL + '?search_type=workflow';
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

    function get_enqueued_objects(workflow_node_id){

        var enqueued_objects = new Object();
        enqueued_objects.record_names = [];
        enqueued_objects.record_ids = {};
        enqueued_objects.priority = null;
        enqueued_objects.enqueued_object_class = null;

        var url = GET_ENQUEUED_OBJECTS_URL + '?workflow_node_id=' + workflow_node_id;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(data.success){
                enqueued_objects.record_names = data.record_names;
                enqueued_objects.record_ids = data.record_ids;
                enqueued_objects.priority = data.priority;
                enqueued_objects.enqueued_object_class = data.enqueued_object_class;
            }
            else {
                alert('someting went wrong getting enqueued objects - ' + data.message);
            }
        });

        return enqueued_objects;
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

    function is_selected_option(selected, id, key){
        option_selected = '';

        if((id in search_criteria)  && (id in selected) && (key in selected[id])){
            option_selected = 'selected';
        }

        return option_selected;
    }

    function multiselect_init(id){

        $('#' + id).multiselect({
            maxHeight: "350",
            buttonWidth: '300px',
            enableCaseInsensitiveFiltering: true
        });
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

    function set_search_html(dialog){
        dialog.empty();

        var search_data = get_workflow_search_data();
        var html = '<div><table>';

        var selected = get_selected_search();

        html+= add_select_dropdown_html(search_data['workflow_ids'], 'Id', 'workflow_ids', selected);
        html+= add_select_dropdown_html(search_data['workflow_names'], 'Name', 'workflow_names', selected);
        html+= add_select_dropdown_html(search_data['disabled'], 'Disabled', 'disabled', selected);
        html+= add_select_dropdown_html(search_data['use_pbs'], 'Use PBS', 'use_pbs', selected);

        html+= '</table></div>';

        dialog.append(html);

        multiselect_init('workflow_ids');
        multiselect_init('workflow_names');
        multiselect_init('disabled');
        multiselect_init('use_pbs');
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
        var url = 'workflows';

        var selected_criteria = get_selected_criteria();
        url = set_url_with_criteria(url, selected_criteria);

        return url;
    }

    function set_create_job_html(enqueued_objects, id, type){

        var html = '<div id="create_workflow_job_dialog_' + id + '"><div class= "create_job_error_messages" id="create_job_error_messages_'+ id + '"></div>';
        html+= '<table>';
        html+='<tr><th>Enqueued Object Class</th><th>'+ enqueued_objects.enqueued_object_class + '</th></tr>';
        html+='<tr><th>Enqueued Object*</th><th><input id="' + get_create_update_id(id, type, 'enqueued_object') +'" type="text" name="enqueued_objects"></th></tr>';
        html+='<tr><th>Priority*</th><th><input id="' + get_create_update_id(id, type, 'priority') +'" type="text" name="priority" value="' + enqueued_objects.priority + '"></th></tr>';
        html+= '</table></div>';

        return html;
    }

    function get_create_update_id(id, type, key){
        return (type + '_' + id + '_' + key)
    }

    function show_auto_complete_event(event){
        $("#" + event.data.id).trigger( "focus" );
        $("#" + event.data.id).autocomplete("search", "");
    }

    function add_enqueued_object_lookahead(id, type, enqueued_objects){
        var enqueued_object_class_id = get_create_update_id(id, type, 'enqueued_object');

        var input = $('#' + enqueued_object_class_id);

        input.autocomplete({
            source: enqueued_objects.record_names,
            minLength:0
        });

        input.click({id: enqueued_object_class_id}, show_auto_complete_event);
    }

    function create_job_record(id, type, enqueued_objects, workflow_node_id){

        var enqueued_object = $('#' + get_create_update_id(id, type, 'enqueued_object')).val();
        var priority = $('#' + get_create_update_id(id, type, 'priority')).val();

        var enqueued_object_id = enqueued_objects.record_ids[enqueued_object];


        var url = CREATE_JOB_URL + '?priority=' + priority + '&enqueued_object_id=' + enqueued_object_id + '&workflow_node_id=' + workflow_node_id;

        var request = $.ajax({
            method: "GET",
            url: url,
            dataType: "JSON",
            async: false
        });

        //on success
        request.done(function (data) {
            if(!data.success){
                alert('someting went wrong creating job');
            }
        });

        return true;
    }

    function validate_not_null(id, type, field_name){
        var value_id = get_create_update_id(id, type, field_name);

        var valid = true;

        var item = $('#' + value_id);

        if(item.val().length === ZERO){
            item.addClass('invalid_input')
            var error_message = field_name + ' is a required field';
            var html = '<p>' + error_message + '</p>';
            $('#create_job_error_messages_'+ id).append(html);
            valid = false;
        }

        return valid;
    }

    function validate_range(id, type, field_name, min, max){
        var value_id = get_create_update_id(id, type, field_name);
        var valid = true;

        var item = $('#' + value_id);

        if(Number(item.val()) < min || Number(item.val()) > max){
            item.addClass('invalid_input')
            var error_message = field_name + ' must be between ' + min + ' and ' + max;
            var html = '<p>' + error_message + '</p>';
            $('#create_job_error_messages_'+ id).append(html);
            valid = false;
        }

        return valid;
    }

    function is_integer(number){
        var value = Math.floor(Number(number));
        return String(value) === number;
    }


    function validate_integer(id, type, field_name){
        var value_id = get_create_update_id(id, type, field_name);
        var valid = true;

        var item = $('#' + value_id);

        if(!is_integer(item.val())){
            item.addClass('invalid_input')
            var error_message = field_name + ' must be an integer';
            var html = '<p>' + error_message + '</p>';
            $('#create_job_error_messages_'+ id).append(html);
            valid = false;
        }

        return valid;
    }

    function validate_acceptable_field(id, type, field_name, acceptable_records){
        var value_id = get_create_update_id(id, type, field_name);
        var item = $('#' + value_id);
        var value = item.val();
        var valid = false;

        for(var i = ZERO; !valid && i < acceptable_records.length; i++){

            if(value.toString() === acceptable_records[i].toString()){
                valid = true;
            }
        }

        if(!valid){
            item.addClass('invalid_input')
            var error_message = value + ' is not a valid option for ' + field_name;
            var html = '<p>' + error_message + '</p>';
            $('#create_job_error_messages_'+ id).append(html);
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
            $('#create_job_error_messages_'+ id).append(html);
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

    function validate_save(id, type, valid_objects){
        var valid = true;

        //clear old messages
        $('#create_job_error_messages_'+ id).empty()
        $('.save_update').removeClass('invalid_input')
        $('.save_update_node').removeClass('invalid_input')
        $('.save_update_workflow').removeClass('invalid_input')

        if(type === 'workflow'){
            valid = validate_not_null(id, type, 'enqueued_object') && valid;
            valid = validate_not_null(id, type, 'priority') && valid;
            valid = validate_integer(id, type, 'priority') && valid;
            valid = validate_range(id, type, 'priority', ZERO, ONE_HUNDRED) && valid;
            valid = validate_acceptable_field(id, type, 'enqueued_object', valid_objects) && valid
        }
        else if(type === 'workflow_node_show'){
            valid = validate_not_null(id, type, 'max_retries') && valid;
            valid = validate_not_null(id, type, 'batch_size') && valid;
            valid = validate_not_null(id, type, 'priority') && valid;
            valid = validate_integer(id, type, 'max_retries') && valid;
            valid = validate_integer(id, type, 'batch_size') && valid;
            valid = validate_integer(id, type, 'priority') && valid;
            valid = validate_range(id, type, 'max_retries', ZERO, ONE_HUNDRED_THOUSAND) && valid;
            valid = validate_range(id, type, 'batch_size', ZERO, ONE_HUNDRED_THOUSAND) && valid;
            valid = validate_range(id, type, 'priority', ZERO, ONE_HUNDRED) && valid;
        }
        else if(type === 'workflow_show'){
            valid = validate_not_null(id, type, 'name') && valid;
            valid = validate_unique(id, type, 'name') && valid;
        }

        return valid;
    }

    function create_job(workflow_node_id, workflow_id){
        var html_id = 'create_workflow_job_dialog_' + workflow_node_id;
        var dialog = $("#" + html_id);

        if(dialog.length !== ZERO){
            if(!dialog.dialog("isOpen")){
                dialog.dialog("open");
            }
        }
        else{

            var type = 'workflow';
            var enqueued_objects = get_enqueued_objects(workflow_node_id);

            if(enqueued_objects.record_names !== null && enqueued_objects.record_ids){
                var html = set_create_job_html(enqueued_objects, workflow_node_id, type);

                var title = 'Create new job';

                $(function() {
                    $(html).dialog({
                        title: title,
                        width:'auto',
                        height:'auto',
                        create: function(){
                            add_enqueued_object_lookahead(workflow_node_id, type, enqueued_objects);
                        },
                        buttons: {
                          Save: function() {
                            var valid = validate_save(workflow_node_id, type, enqueued_objects.record_names);
                            if(valid){
                                var success = create_job_record(workflow_node_id, type, enqueued_objects, workflow_node_id);
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

    function get_workflow_node_ids_on_page(){
        var ids = [];
        $('.workflow_node').each(function() {
            ids.push($(this).attr('node_id'));
        });

        return ids;
    }

    function update_workflow_node_status(){

        var ids = get_workflow_node_ids_on_page();
        if(ids.length > 0){
            

            var url = WORKFLOW_STATUS_URL + '?workflow_node_ids=' + ids.join(',');

            var request = $.ajax({
                method: "GET",
                url: url,
                dataType: "JSON",
                async: false
            });

            // //on success
            request.done(function (data) {
                if (data.success){
                    var payload = data.payload
                    for(var node_id in payload){
                        var node_data = payload[node_id]
                        var name = node_data['name']
                        var node_color_class = node_data['node_color_class']

                        var node = $('#node_' + node_id);
                        node.removeClass('failed_state')
                        node.removeClass('running_state')
                        node.removeClass('success_state')
                        node.empty()
                        node.addClass(node_color_class)

                        var html = '<p class="workflow_node_header">' + name + '</p>';
                        node.append(html);

                    }
                }
            });
        }
    }

    function init(workflows, milliseconds_between_refresh) {
        for(var index = 0; index < workflows.length; index++){
            create_tree(workflows[index]);
        }

        set_show_node_dialog_click_handlers();
        set_workflow_dialog_click_handlers();
        window.setInterval(update_workflow_node_status, milliseconds_between_refresh);
    }

}