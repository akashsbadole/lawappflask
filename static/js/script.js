// Custom JavaScript for Law Firm Management System

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
    
    // Confirmation for delete actions
    $('.delete-confirm').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
        }
    });
    
    // Form validation
    $('form').on('submit', function(e) {
        var form = $(this);
        if (form[0].checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.addClass('was-validated');
    });
    
    // Date picker initialization
    $('.date-picker').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true
    });
    
    // Time picker initialization
    $('.time-picker').timepicker({
        showSeconds: false,
        showMeridian: false,
        minuteStep: 15
    });
    
    // File upload preview
    $('.file-upload').on('change', function() {
        var fileName = $(this).val().split('\\').pop();
        $(this).next('.custom-file-label').html(fileName);
    });
    
    // Search functionality
    $('#search-input').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('#search-results .search-item').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
    
    // Tab navigation
    $('.nav-tabs a').on('click', function(e) {
        e.preventDefault();
        $(this).tab('show');
    });
    
    // Modal handling
    $('.modal').on('show.bs.modal', function(e) {
        var button = $(e.relatedTarget);
        var modal = $(this);
        
        // Load content dynamically if needed
        var url = button.data('url');
        if (url) {
            modal.find('.modal-content').load(url);
        }
    });
    
    // AJAX form submission
    $('.ajax-form').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var url = form.attr('action');
        var method = form.attr('method');
        var data = form.serialize();
        
        $.ajax({
            url: url,
            method: method,
            data: data,
            success: function(response) {
                // Handle success response
                if (response.success) {
                    showAlert('success', response.message);
                    // Close modal if form is in modal
                    form.closest('.modal').modal('hide');
                    // Refresh data if needed
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    }
                } else {
                    showAlert('danger', response.message || 'An error occurred');
                }
            },
            error: function(xhr) {
                // Handle error response
                showAlert('danger', 'An error occurred. Please try again.');
            }
        });
    });
    
    // Dynamic table sorting
    $('.sortable-table').on('click', 'th.sortable', function() {
        var table = $(this).parents('table');
        var rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()));
        this.asc = !this.asc;
        if (!this.asc) {
            rows = rows.reverse();
        }
        for (var i = 0; i < rows.length; i++) {
            table.append(rows[i]);
        }
    });
    
    // Dynamic table filtering
    $('.table-filter').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $(this).parents('.table-container').find('tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
    
    // Print functionality
    $('.print-btn').on('click', function() {
        window.print();
    });
    
    // Export functionality
    $('.export-btn').on('click', function() {
        var format = $(this).data('format');
        var url = $(this).data('url');
        
        if (format && url) {
            window.open(url + '?format=' + format, '_blank');
        }
    });
    
    // Auto-save functionality
    var autoSaveTimer;
    $('.auto-save').on('input', function() {
        clearTimeout(autoSaveTimer);
        var input = $(this);
        autoSaveTimer = setTimeout(function() {
            saveField(input);
        }, 1000);
    });
    
    // Notification handling
    $('.notification-btn').on('click', function() {
        var url = $(this).data('url');
        $.get(url, function(data) {
            $('#notification-container').html(data);
        });
    });
    
    // Keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl+N for new item
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            $('.new-item-btn').first().click();
        }
        
        // Ctrl+S for save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            $('.save-btn').first().click();
        }
        
        // Escape to close modal
        if (e.key === 'Escape') {
            $('.modal.show').modal('hide');
        }
    });
});

// Helper functions
function showAlert(type, message) {
    var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
                    message +
                    '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                    '</div>';
    
    $('.alert-container').prepend(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').first().fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

function comparer(index) {
    return function(a, b) {
        var valA = getCellValue(a, index);
        var valB = getCellValue(b, index);
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.toString().localeCompare(valB);
    };
}

function getCellValue(row, index) {
    return $(row).children('td').eq(index).text();
}

function saveField(input) {
    var url = input.data('save-url');
    var value = input.val();
    var field = input.attr('name');
    
    $.post(url, {
        field: field,
        value: value
    }, function(response) {
        if (response.success) {
            input.addClass('is-valid');
            setTimeout(function() {
                input.removeClass('is-valid');
            }, 2000);
        }
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-IN');
}

function formatDateTime(datetime) {
    return new Date(datetime).toLocaleString('en-IN');
}

// Chart initialization
function initChart(elementId, type, data, options) {
    var ctx = document.getElementById(elementId).getContext('2d');
    return new Chart(ctx, {
        type: type,
        data: data,
        options: options
    });
}

// DataTable initialization
function initDataTable(elementId, options) {
    return $(elementId).DataTable(options);
}

// Full calendar initialization
function initCalendar(elementId, options) {
    return $(elementId).fullCalendar(options);
}