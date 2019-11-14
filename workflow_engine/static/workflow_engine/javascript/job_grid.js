// var $ = django.jQuery;

function draw_grid(msg) {
    //var schema = msg['schema'];
    var qnames = msg['workflow_node'];
    var node_order = msg['node_order'];

    var run_state_class = {
            "p": "run_state_pending",
            "q": "run_state_queued",
            "r": "run_state_running",
            "s": "run_state_success",
            "x": "run_state_failed_execution",
            "f": "run_state_failed",
            "k": "run_state_process_killed",
        }; 

    var run_state_abbr = {
            "PENDING": " P ",
            "QUEUED": " Q ",
            "RUNNING": " R ",
            "SUCCESS": " S ",
            "FAILED_EXECUTION": " FE ",
            "FAILED": " F ",
            "PROCESS_KILLED": " K ",
        }; 

    var object_state_class = {
            "PENDING": "pending",
            "PROCESSING": "processing",
            "MONTAGE_QC": "montage_qc",
            "REIMAGE": "reimage",
            "MONTAGE_QC_FAILED": "montage_qc_failed",
            "MONTAGE_QC_PASSED": "montage_qc_passed",
            "REDO_POINT_MATCH": "redo_point_match",
            "REDO_SOLVER": "redo_solver",
            "FAILED": "failed",
            "GAP": "gap"
        };
 
    var section_row = $("<tr></tr>");

    var queue_td = $("<td></td>").text('Z index');
    section_row.append(queue_td);

    queue_td = $("<td></td>").text('Mapped Z');
    section_row.append(queue_td);
    queue_td = $("<td></td>").text('state');
    section_row.append(queue_td);

//    var queue_td = $("<td></td>").text('reindex');
    section_row.append(queue_td);

    queue_td = $("<td></td>").text('chunks');
    section_row.append(queue_td);

    var idx = 0;
    for (idx = 0; idx < node_order.length; idx++) {
        queue_td = $("<td></td>").text(qnames[node_order[idx]]);
        section_row.append(queue_td);
    }
    $('#grid_table').append(section_row)

    var totals_row = $("<tr></tr>");
    var total_td = $("<td></td>").text('totals');
    totals_row.append(total_td);
    var spacer_td = $("<td colspan=3></td>");
    totals_row.append(spacer_td);

//  TODO: totals
//    var idx = 0;
//    var qlen = qnames.length;
//    var totals = msg.pop()
//    for (idx = 0; idx < qlen; idx++) {
//        total_td = $("<td></td>").text(totals[qnames[idx]]);
//        totals_row.append(total_td);
//    }

//    $('#grid_table').append(totals_row)

    var last_z = -1
    var current_z = -1

    var TEMP_Z_POS = 0
    var REAL_Z_POS = 1
    var OBJECT_STATE_POS = 2
    var NODE_ID_POS = 3
    var RUN_STATE_POS = 4
    var JOB_ID_POS = 5
    var OBJECT_TYPE_POS = 6
    var OBJECT_ID_POS = 7
    var START_TIME_POS = 8
    var END_TIME_POS = 9

//    var zlen = msg.length;
    var msg_data = msg['data']
    var object_states = msg['object_state']

    section_row = $("<tr></tr>");
    var job_tds = Array();

    for (var i in msg_data) {
        var entry = msg_data[i]
        current_z = entry[TEMP_Z_POS]

        if (current_z != last_z) {
            for (var i = 0; i < node_order.length; i++) {
                var node_id = node_order[i];

                if (node_id in job_tds) {
                    var job_td = job_tds[node_id];
                    if (job_td.data('start') < latest_time) {
                        job_td.addClass('outdated');
                    }
                    if (job_td.data('end') > latest_time) {
                        latest_time = job_td.data('end');
                    }
                    section_row.append(job_td);
                } else {
                    blank_td = $("<td></td>").text("-");
                    section_row.append(blank_td);
                }
            }
            $('#grid_table').append(section_row)

            if ((last_z > -1) && ((current_z - last_z) > 1)) {
                skip_row = $('<tr><td colspan="200" height="2">&nbsp;</td></tr>');
                $('#grid_table').append(skip_row)
            }

            section_row = $("<tr></tr>");
            job_tds = Array();
            latest_time = 0;

            var index_td = $("<td></td>").text(current_z);
            section_row.append(index_td);

            index_td = $("<td></td>").text(entry[REAL_Z_POS]);
            section_row.append(index_td)

            var object_state_text = object_states[
                entry[OBJECT_STATE_POS]
            ]
            var object_state_td = $("<td></td>").text(object_state_text);

            try {
                object_state_td.attr(
                    'class',
                    object_state_class[object_state_text]);
            } catch (err) {
                object_state_td.attr('class', 'object_state_unknown');
            }

            section_row.append(object_state_td);

    //        var reimage_text = ' '
    //        if (current_z == last_z) {
    //            reimage_text = 'X'
    //        }
    //        var reimage_td = $('<td align="center"></td>').text(reimage_text);
    //        section_row.append(reimage_td);

            var chunk_text = ""; // msg[i]['chunks']
            var chunk_td = $("<td></td>").text(chunk_text);
            section_row.append(chunk_td);

            last_z = current_z
        }

        var node_id = entry[NODE_ID_POS]
        var job_id = entry[JOB_ID_POS];
        var run_state_text = entry[RUN_STATE_POS];
        var object_type = entry[OBJECT_TYPE_POS];
        var object_id = entry[OBJECT_ID_POS];
        var start = Date.parse(entry[START_TIME_POS]);
        var end = Date.parse(entry[END_TIME_POS])

        run_state_td = $("<td></td>");
        run_state_td.data('start', start);
        run_state_td.data('end', end);

        if (job_id != -1) {
            var run_state_link = $("<a>");
            run_state_link.attr(
                "href",
                "/admin/workflow_engine/job/" + job_id);
            run_state_link.attr("title", current_z)
            run_state_link.text(run_state_text);
            run_state_td.append(run_state_link);

            var em_montage_link = $("<a>");
            em_montage_link.attr(
                "href",
                "/admin/at_em_imaging_workflow/" + object_type + "/" + object_id);
            em_montage_link.text('(' + object_id + ')');
            run_state_td.append(em_montage_link);

            var run_state_legacy_link = $("<a>");
            run_state_legacy_link.attr(
                "href",
                "/workflow_engine/jobs?job_ids=" + job_id);
            run_state_legacy_link.attr(
                "title",
                "Open start/kill view for " + job_id + " in new tab");
            run_state_legacy_link.text(' O ');
            run_state_td.append(run_state_legacy_link)

            // run state and montage set links open in admin tab/window
            run_state_link.attr("target", "workflow_admin");
            run_state_legacy_link.attr("target", "workflow_admin");
            em_montage_link.attr("target", "workflow_admin");

            try {
                run_state_td.attr(
                    'class',
                    run_state_class[run_state_text]);
            } catch (err) {
                run_state_td.attr('class', 'run_state_unknown');
            }
        }

        job_tds[node_id] = run_state_td;
    }
}

function render_progress_grid(z_min, z_max) {
    tape_uid = $('#load').val()
    progress_url = '/at_em/faster_job_grid?tape=' + tape_uid + '&z_min=' + String(z_min) + '&z_max=' + String(z_max);
    fetch(progress_url, {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
    })
    .then((response) => {
        response.json().then(msg => {
            draw_grid(msg)
        }).catch(err => {
            $('#grid_table').empty();
        })
    })
}

$(document).ready(function() {
    $('#slider_div').slider({
        orientation: "vertical",
        range: "min",
        min: 0,
        max: 10000,
        value: 5000,
        slide: function(event, ui) {
            z = 10000 - $("#slider_div").slider("value");
            $("#amount").val(z);
        },
        stop: function(event, ui) {
            z = parseInt($("#amount").val());
            $('#grid_table').empty();
            render_progress_grid(z, z+30);
        }
    });
    $('#btn_refresh').click(function() {
        z = parseInt($('#amount').val());
        $('#grid_table').empty();
        render_progress_grid(z, z+30);
    });

    // setInterval(render_progress_grid, 15*1000)
});
