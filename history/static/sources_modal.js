function loadSource(source) {
    if(source.save_files?.length > 0) {
        document.getElementById('saved-modal-holder').innerHTML = `<p class="lead">Save Files</p><div id="saved-modal-table"></div>`

        prepareSaveTable()
    
        for(let save of source.save_files) {
            document.getElementById('saved-modal-tbody').appendChild(renderSaveRecord(save))
        }
    }

    if(source.server_responses?.length > 0) {
        $('#server-modal-holder').html(`<p class="lead">Server Responses</p><div id="server-modal-table"></div>`)

        prepareServerTable()

        for(let response of source.server_responses) {
            document.getElementById('server-modal-tbody').appendChild(renderServerRecord(response))
        }
    }

    if(source.manual_submissions?.length > 0) {
        $('#manual-modal-holder').html(`<p class="lead">Manual Submissions</p><div id="manual-modal-table">Use the other modal to see the manual submission info</div>`)
    }
}

function prepareSaveTable() {
    header = `<table class="table table-striped">
					<thead>
						<tr>
							<th>PK</th>
                            <th>Uploader</th>
                            <th>Submitted</th>
                            <th>Created</th>
                            <th>Player Name</th>
                            <!--<th>Player User ID</th>
                            <th>Player Account ID</th>
                            <th>Binary Version</th>
                            <th>Levels<br><small><small>(no&nbsp;blanks)</small></small></th>-->
                            <th>Levels (all)</th>
						</tr>
					</thead>
					<tbody id="saved-modal-tbody">
					</tbody>
				</table>`
    document.getElementById('saved-modal-table').innerHTML = header
}

function renderSaveRecord(record) {
    const tr = document.createElement('tr')

    tr.appendChild(td(record.id, `/submission/${record.id}/`))
    tr.appendChild(td(record.author))
    tr.appendChild(td(record.submitted))
    tr.appendChild(td(record.created))
    tr.appendChild(td(record.player_name))
    /*tr.appendChild(td(record.player_user_id))
    tr.appendChild(td(record.player_account_id))
    tr.appendChild(td(record.binary_version))
    tr.appendChild(td(record.levels_no_blanks))*/
    tr.appendChild(td(record.count))

    return tr
}

function prepareServerTable() {
    header = `<table class="table table-striped">
					<thead>
						<tr>
							<th>Created</th>
                            <th>Endpoint</th>
                            <th>Comment</th>
                            <th>Get Type</th>
                            <th>Get Page</th>
						</tr>
					</thead>
					<tbody id="server-modal-tbody">
					</tbody>
				</table>`
    document.getElementById('server-modal-table').innerHTML = header
}

function renderServerRecord(record) {
    const tr = document.createElement('tr')

    tr.appendChild(td(record.created))
    tr.appendChild(td(record.endpoint))
    tr.appendChild(td(record.comment))
    tr.appendChild(td(record.get_type))
    tr.appendChild(td(record.get_page))

    return tr
}