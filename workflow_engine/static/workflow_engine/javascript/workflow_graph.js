
function draw_workflow1(workflow_nodes, workflow_edges) {
    alert(workflow_nodes);
}

function node_color(n, state_hash, run_states) {
    reverse_run_states = {}
    node_index = n.toString()

    Object.keys(run_states).forEach(
        s => {
            reverse_run_states[run_states[s.toString()]] = s
        }
    )

    failed = '[' + node_index + ',' + reverse_run_states['FAILED'] + ']';
    failed_execution = '[' + node_index + ',' + reverse_run_states['FAILED_EXECUTION'] + ']';
    process_killed = '[' + node_index + ',' + reverse_run_states['PROCESS_KILLED'] + ']';
    running = '[' + node_index + ',' + reverse_run_states['RUNNING'] + ']';
    pending = '[' + node_index + ',' + reverse_run_states['PENDING'] + ']';
    queued = '[' + node_index + ',' + reverse_run_states['QUEUED'] + ']';

    try {
        if ((state_hash[failed] > 0) ||
            (state_hash[failed_execution] > 0) ||
            (state_hash[process_killed] > 0)) {
            return 'red';
        } else if (
            (state_hash[running] > 0) ||
            (state_hash[pending] > 0) ||
            (state_hash[queued] > 0)) {
            return 'green';
        } else if (
            (state_hash[failed] > 0)) {
            return 'blue';
        } else {
            return 'blue';
        }
    } catch(err) {
        return 'grey';
    }
}


function color_nodes(
    job_queues, batch_size, run_states, counts, pending_queued_running, totals) {
    state_hash = {};

    var cy_nodes = window.cy.nodes()

    for (i = 0; i < cy_nodes.length; i++) {
        node_id = cy_nodes[i].data()['id'].toString();
        job_queue_name = job_queues[node_id].replace(/ /g, '\n');
        state_color = node_color(node_id, counts, run_states);
        cy_nodes[i].classes(state_color + 'Class');

        node_number_string = '(' + totals[node_id] + ') ' + pending_queued_running[node_id] + ' / ' + batch_size[node_id]
        cy_nodes[i].data(
            'job_queue_name',
            job_queue_name
        )
        cy_nodes[i].data(
            'node_id',
            node_id
        )
        cy_nodes[i].data(
            'label',
            job_queue_name + '\n' + node_number_string
        )
    }
}

function node_summary_tables(
    job_queues, batch_size, run_states, counts, pending_queued_running, totals) {

    var reverse_run_states = {};
    $.each(run_states, function(run_state_id, run_state_name) {
        reverse_run_states[run_state_name] = run_state_id;
    });

    var run_state_order = [
        "PENDING",
        "QUEUED",
        "RUNNING",
        "FINISHED_EXECUTION",
        "FAILED_EXECUTION",
        "FAILED",
        "SUCCESS",
        "PROCESS_KILLED"
    ];

    $('div.info').empty();

    $.each(job_queues, function(node_id, node_name) {
        var node_tbl = $('<table>').attr('border', 1).width('300px');
        node_tbl.data('node_id', node_id.toString());

        var tr = $('<tr>').append(
            $('<td>').text(node_name).attr('colspan', 2)
        );
        node_tbl.append(tr);

        $.each(run_state_order, function(run_state_order, run_state_name) {
            var run_state_index = reverse_run_states[run_state_name];
            var count_index = '[' + node_id + ',' + run_state_index + ']';
            var tr = $('<tr>').append(
                $('<td>').text(run_state_name)
            ).append(
                $('<td>').text(counts[count_index])
            );
            node_tbl.append(tr);
        });

        node_tbl.addClass('node_info').css({'float': 'left'}).hide();
        $('div.info').append(node_tbl);
    });
}

function draw_workflow(workflow_nodes, workflow_edges) {
var cy = window.cy = cytoscape({
  container: document.getElementById('cy'),

  boxSelectionEnabled: false,
  autounselectify: true,

  layout: {
    name: 'dagre',
    fit: false,
    transform: function( node, pos ) { return { x: pos['y'], y: pos['x'] }; },
    spacingFactor: 0.75
  },

  zoom: 0.5,

  style: [
    {
      selector: 'node',
      style: {
        'shape': 'roundrectangle',
        'content': 'data(label)',
        'font-size': '10px',
        'font-weight': 'bold',
        'text-opacity': 0.6,
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        //'text-max-width': 50,
        'width': 60,
        'height': 60,
      }
    },

    {
      selector: '.focused',
      style: {
        'border-color': 'red',
      }
    },

    {
      selector: 'edge',
      style: {
        'curve-style': 'bezier',
        'width': 4,
        'target-arrow-shape': 'triangle',
        'line-color': 'steelblue',
        'opacity': 0.3,
        'target-arrow-color': 'steelblue'
      }
    },

    {
        selector: '.redClass',
        style: {
        'background-color': 'lightcoral',
        'shape': 'rectangle'
       }
    },
    {
        selector: '.greenClass',
        style: {
        'background-color': 'lightgreen',
        'shape': 'rectangle'
       }
    },
    {
        selector: '.blueClass',
        style: {
        'background-color': 'lightblue',
        'shape': 'rectangle'
       }
    },
    {
        selector: '.greyClass',
        style: {
        'background-color': 'lightgrey',
        'shape': 'rectangle'
       }
    }
    ],

  elements: {
    nodes: Object.keys(workflow_nodes).map(
        n => {
            return {
                data: {
                    id: n,
                    label: workflow_nodes[n]
                },
                classes: 'multiline-manual'
            } }),
    edges: workflow_edges.map(
        e => {
            return {
                data: {
                    source: e[0],
                    target: e[1]
                }
            } }),
  },
});

cy.on('click', 'node', function(e) {
    tgt = e.cyTarget
    
    if (tgt === cy) {
    } else {
        node_id = e.target.data()['node_id'];
        // url = 'http://ibs-timf-ux1.corp.alleninstitute.org:9001/admin/workflow_engine/job/?run_state__name=PROCESS_KILLED&workflow_node__job_queue__name=Load+Z+Mapping';
        $('table.node_info').each(function(i, tbl) {
           tbl = $(tbl)
           if (tbl.data('node_id') == node_id) {
               tbl.show();
           } else {
               tbl.hide();
           }
        });
    }
});

}


function render_workflow_graph() {
    graph_url = '/workflow_engine/workflows/monitor_data';

    fetch(graph_url, {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
    .then((response) => {
        response.json().then(obj => {
            draw_workflow(obj['job_queue_name'], obj['edges']);
            node_summary_tables(
                    obj['job_queue_name'],
                    obj['batch_size'],
                    obj['run_state_name'],
                    obj['count'],
                    obj['pending_queued_running'],
                    obj['total']
                );
            color_nodes(
                obj['job_queue_name'],
                obj['batch_size'],
                obj['run_state_name'],
                obj['count'],
                obj['pending_queued_running'],
                obj['total']
            );
        })
    })
}


var $ = django.jQuery;
$(document).ready(function(){
    render_workflow_graph();
    //setInterval(render_workflow_graph, 5000);
})
