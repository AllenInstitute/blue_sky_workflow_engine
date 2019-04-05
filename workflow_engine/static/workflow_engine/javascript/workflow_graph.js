
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
            'label',
            job_queue_name + '\n' + node_number_string
        )
    }
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

  zoom: 1,

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
    setInterval(render_workflow_graph, 5000);
})
