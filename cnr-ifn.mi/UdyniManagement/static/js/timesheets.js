// Add classes to element
function addClasses(element, classes) {
    if(Array.isArray(classes)) {
        classes.forEach(function(cls) {
            element.addClass(cls);
        });
    } else {
        element.addClass(classes);
    }
    return element;
}

// Create table
function createTable(parent, classes) {
    table = $('<table cellspacing="0" cellpadding="0"></table>');
    addClasses(table, classes);
    table.appendTo(parent);
    return table;
}

// Create header
function addHeader(parent) {
    header = $('<thead></thead>');
    header.appendTo(parent);
    return header;
}

// Create body
function addBody(parent) {
    body = $('<tbody></tbody>');
    body.appendTo(parent);
    return body;
}

// Create a table line
function addLine(parent, classes) {
    line = $('<tr></tr>');
    addClasses(line, classes);
    line.appendTo(parent);
    return line;
}

// Create header cell
function addHeaderCell(line, classes, content) {
    cell = $('<th></th>');
    addClasses(cell, classes);
    if (typeof(content) === 'object') {
        content.appendTo(cell);
    } else {
        cell.text(content);
    }
    cell.appendTo(line);
    return cell;
}

// Create a table cell
function addCell(line, classes, id, content) {
    cell = $('<td></td>');
    if(id !== null) {
        cell.attr('id', id);
    }
    addClasses(cell, classes);
    if (typeof(content) === 'object') {
        content.appendTo(cell);
    } else {
        cell.text(content);
    }
    cell.appendTo(line);
    return cell;
}

function format_ts_table(root, ts) {

    // Create table
    table = createTable(root, 'timesheet');

    // Add header
    thead = addHeader(table);
    days_line = addLine(thead, 'days');
    addHeaderCell(days_line, 'header', 'Day');

    ts.days.forEach(function(day) {
        cls = ['day', ]
        if(day.holiday) {
            cls.push('holiday');
        }
        addHeaderCell(days_line, cls, day.n);
    });

    addHeaderCell(days_line, ['day', 'total'], 'Σ');
    addHeaderCell(days_line, ['day', 'hours'], 'ε');
    addHeaderCell(days_line, ['day', 'total'], 'Total');

    // Add body
    tbody = addBody(table);

    // Cycle through projects
    ts.projects.forEach(function(p, i) {

        // Add line
        cls = ['project']
        if(p.has_wps)
            cls.push('has_wps');
        line = addLine(tbody, cls);

        // Project name
        addCell(line, 'header', null, p.name + ': ' + p.ref);

        // Add hours for each day
        p.days.forEach(function(d, k) {
            // Select classes
            cls = ['hours', ]
            if(ts.days[k].holiday)
                cls.push('holiday');
            if(!ts.days[k].holiday && ts.days[k].code == '' && p.id != -1 && !p.has_wps)
                cls.push('editable-cell');
            if(d < 0)
                cls.push('sum-mismatch');

            // Format ID
            id = null;
            if(!ts.days[k].holiday && (ts.days[k].mission || ts.days[k].code == '')) {
                if(p.has_wps) {
                    id = 'ps_' + i + '_' + k;
                } else {
                    id = 'rp_' + p.id + '_' + k + '_' + i;
                }
            }

            // Create cell
            addCell(line, cls, id, d.toFixed(1));
        });

        eps = p.sum - p.total;
        if(p.has_wps) {
            addCell(line, ['hours', 'total'], 'pssum_' + i, p.sum.toFixed(1));
            cls = ['hours', ]
            if(Math.abs(eps) > 0.01)
                cls.push('sum-mismatch');
            addCell(line, cls, 'pserr_' + i, eps.toFixed(1));
            addCell(line, ['hours', 'total'], 'pstot_' + i, p.total.toFixed(1));

        } else {
            if(p.id != -1) {
                addCell(line, ['hours', 'total'], 'sum_' + p.id, p.sum.toFixed(1));
                cls = ['hours', ]
                if(Math.abs(eps) > 0.01)
                    cls.push('sum-mismatch');
                addCell(line, cls, 'err_' + p.id, eps.toFixed(1));
            } else {
                addCell(line, 'total', null, '');
                addCell(line, 'hours', null, '');
            }
            addCell(line, ['hours', 'total'], 'tot_' + p.id, p.total.toFixed(1));
        }

        // Add WPs if present
        if(p.has_wps) {
            p.wps.forEach(function(wp, j) {
                cls = ['wp', ];
                if(wp.last)
                    cls.push('last_wp');
                line = addLine(tbody, cls);

                c = addCell(line, 'header', null, wp.name);
                c.attr('data-toggle', 'tooltip');
                c.attr('title', wp.desc);

                wp.days.forEach(function(d, k) {
                    // Select classes
                    cls = ['hours', ]
                    if(ts.days[k].holiday)
                        cls.push('holiday');
                    if(ts.days[k].code == '' && !ts.days[k].holiday)
                        cls.push('editable-cell');
                    if(d < 0)
                        cls.push('sum-mismatch');

                    // Format ID
                    id = null;
                    if(!ts.days[k].holiday && (ts.days[k].mission || ts.days[k].code == '')) {
                        id = 'rp_w' + wp.id + '_' + k + '_' + i;
                    }

                    // Create cell
                    addCell(line, cls, id, d.toFixed(1));
                });

                eps = wp.sum - wp.total
                addCell(line, ['hours', 'total'], 'sum_w' + wp.id, wp.sum.toFixed(1));
                cls = ['hours', ]
                if(Math.abs(eps) > 0.01)
                    cls.push('sum-mismatch');
                addCell(line, cls, 'err_w' + wp.id, eps.toFixed(1));
                addCell(line, ['hours', 'total'], 'tot_w' + wp.id, wp.total.toFixed(1));
            });
        }
    });

    // Absences line
    line = addLine(tbody, 'absences');
    addCell(line, 'header', null, 'Absences');
    ts.days.forEach(function(d) {
        cls = ['value', ];
        if(d.holiday)
            cls.push('holiday');
        addCell(line, cls, null, d.code);
    });
    addCell(line, 'total', null, '');
    addCell(line, 'hours', null, '');
    addCell(line, 'total', null, '');

    // Totals line
    line = addLine(tbody, 'total');
    addCell(line, 'header', null, 'Total');
    ts.days.forEach(function(d, i) {
        cls = ['hours', ];
        if(d.holiday)
            cls.push('holiday');
        addCell(line, cls, 'dtot_' + i, d.total.toFixed(1));
    });
    addCell(line, 'total', null, '');
    addCell(line, 'hours', null, '');
    addCell(line, ['total', 'hours'], null, ts.grand_total.toFixed(1));

    // Add tooltip handlers
    $('[data-toggle="tooltip"]').tooltip();

    return table;
}

function update_status_message(element, status, error=null) {
    // Check if it has been modified
    element.html("");
    element.removeClass();
    if(status == 'modified') {
        element.addClass("alert").addClass("alert-warning");
        $('<i class="fas fa-triangle-exclamation" aria-hidden="true"></i>').appendTo(element);
        $(document.createTextNode(" Timesheet has been modified since last save")).appendTo(element);
    } else if(status == 'inconsistent') {
        element.addClass("alert").addClass("alert-danger");
        $('<i class="fa-solid fa-hand" aria-hidden="true"></i>').appendTo(element);
        $(document.createTextNode(" Timesheet is inconsistent.")).appendTo(element);
    } else if(status == 'unmodified') {
        element.addClass("alert").addClass("alert-success");
        $('<i class="fas fa-circle-check" aria-hidden="true"></i>').appendTo(element);
        $(document.createTextNode(" Timesheet is consistent and has not been modified since last save")).appendTo(element);
    } else if(status == 'saveok') {
        element.addClass("alert").addClass("alert-success");
        $('<span class="glyphicon glyphicon-ok" aria-hidden="true"></span>').appendTo(element);
        $(document.createTextNode(" Save successful")).appendTo(element);
    } else if(status == 'savefailed') {
        element.addClass("alert").addClass("alert-danger");
        $('<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>').appendTo(element);
        $('<span class="sr-only">Error:</span>').appendTo(element);
        $(document.createTextNode(" Save failed (" + error + ")")).appendTo(element);
    }
}
