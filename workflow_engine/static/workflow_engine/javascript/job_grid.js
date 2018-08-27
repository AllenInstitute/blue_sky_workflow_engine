// var $ = django.jQuery;

function draw_grid(msg) {
    var schema = msg['schema'];
    var qnames = msg['columns'];
    msg = msg['data'];

    var run_state_class = {
            "PENDING": "run_state_pending",
            "QUEUED": "run_state_queued",
            "RUNNING": "run_state_running",
            "SUCCESS": "run_state_success",
            "FAILED_EXECUTION": "run_state_failed_execution",
            "FAILED": "run_state_failed",
            "PROCESS_KILLED": "run_state_process_killed",
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

    var montage_state_class = {
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

    queue_td = $("<td></td>").text('state');
    section_row.append(queue_td);

    queue_td = $("<td></td>").text('chunks');
    section_row.append(queue_td);

    var idx = 0;
    var qlen = qnames.length;
    for (idx = 0; idx < qlen; idx++) {
        queue_td = $("<td></td>").text(qnames[idx]);
        section_row.append(queue_td);
    }
    $('#grid_table').append(section_row)

    var totals_row = $("<tr></tr>");
    var total_td = $("<td></td>").text('totals');
    totals_row.append(total_td);
    var spacer_td = $("<td colspan=2></td>");
    totals_row.append(spacer_td);

    var idx = 0;
    var qlen = qnames.length;
    var totals = msg.pop()
    for (idx = 0; idx < qlen; idx++) {
        total_td = $("<td></td>").text(totals[qnames[idx]]);
        totals_row.append(total_td);
    }

    $('#grid_table').append(totals_row)

    var last_z = -1
    var current_z = -1

    var zlen = msg.length;
    for (var i = 0; i < zlen; i++) {
        current_z = msg[i]['z_index']

        if ((last_z > -1) && ((current_z - last_z) > 1)) {
            skip_row = $('<tr><td colspan="200" height="2">&nbsp;</td></tr>');
            $('#grid_table').append(skip_row)
        }

	last_z = current_z

        section_row = $("<tr></tr>");

        var index_td = $("<td></td>").text(current_z);
        section_row.append(index_td);

        var montage_state_text = msg[i]['workflow_state']
        var montage_state_td = $("<td></td>").text(montage_state_text);

        try {
            montage_state_td.attr(
                'class',
                montage_state_class[montage_state_text]);
        } catch (err) {
            montage_state_td.attr('class', 'montage_state_unknown');
        }
        section_row.append(montage_state_td);

        var chunk_text = msg[i]['chunks']
        var chunk_td = $("<td></td>").text(chunk_text);
        section_row.append(chunk_td);

        for (var j = 0; j < qlen; j++) {
            var qname = qnames[j]

            var job_info = msg[i][qname];
            var job_and_state = [null, null]
            if (job_info) {
                job_and_state = msg[i][qname].split('/');
            }
            var job_id = job_and_state[0];
            var state_name = job_and_state[1];
            var em_montage_set_id = job_and_state[2]

            // pandas can't have ints and NaNs in same columns, so convert
            try {
                em_montage_set_id = Math.floor(em_montage_set_id); 
            } catch(err) {
                em_montage_set_id = -1
            }

            var run_state_text = run_state_abbr[state_name];
            var run_state_td = $("<td></td>");

            if (job_id != null) {
                var run_state_link = $("<a>");
                run_state_link.attr(
                    "href",
                    "/admin/workflow_engine/job/" + job_id);
                run_state_link.attr("title", msg[i]['z_index'])
                run_state_link.text(run_state_text);
                run_state_td.append(run_state_link);

                var em_montage_link = $("<a>");
                em_montage_link.attr(
                    "href",
                    "/admin/development/emmontageset/" + em_montage_set_id);
                em_montage_link.text('(' + em_montage_set_id + ')');
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
                        run_state_class[state_name]);
                } catch (err) {
                    run_state_td.attr('class', 'run_state_unknown');
                }
            }

            section_row.append(run_state_td);
        }
        $('#grid_table').append(section_row)
    }
}

function render_progress_grid() {
    progress_url = '/static/job_grid_data.json';
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

$(document).ready(function(){
    render_progress_grid();
    setInterval(render_progress_grid, 15*1000)
})
