// Service function to reload page
function reload_page() {
  window.location.reload();
}

// Function to load and post a form through ajax using a Bootstrap modal
/* Parameter for the form_options structure:
  'dialog_id': the prefix ID of the modal dialog. Defaults to 'ajax-form'
  'action': the url to get/post the form
  'form_id': the 'id' of form
  'success_action': function called after a successful submission (the function is passed the AJAX response data)
  'post_load_action': function called after loading the form (e.g to connect some jquery functionality)
  'submit': submit button label
  'submiticon': icon for the submit button (is the suffix for FontAwesome solid icons 'fa-<submiticon>')
  'cancel': cancel button label
  'cancelicon': icon for the cancel button (is the suffix for FontAwesome solid icons 'fa-<submiticon>')
  'title': title of the dialog
*/

function check_form_options(form_options) {
  default_form_options = {
    'dialog_id': 'ajax-form',  // NOTE: id with suffix 'dialog' (main dialog), suffix 'content' for dialog content, suffix 'submit' for submit button, suffix 'cancel' for cancel button
    'action': '',
    'form_id': 'default_ajax_form',
    'success_action': null,
    'post_load_action': null,
    'submit': 'Save',
    'submiticon': null,
    'cancel': 'Cancel',
    'cancelicon': null,
    'title': null,
  };
  for(var prop in default_form_options) {
    if(!form_options.hasOwnProperty(prop)) {
      form_options[prop] = default_form_options[prop];
    }
  }
  return form_options;
}

function store_form(object, data, id) {
  // Store HTML in object
  object.html(data);
  // Search for form tag
  form = object.find('form');
  if(form && form.length > 0) {
    // Set ID
    form[0].id = id;
  }
}

function fail_message_dialog(dialog_id, content) {
  $('#'+dialog_id+"-content").html('<div class="card"><div class="card-body alert-danger" role="alert"><i class="fa-solid fa-triangle-exclamation fa-xl mr-2"></i>' + content + '</div></div>');
  $('#'+dialog_id+"-submit").hide();
  $('#'+dialog_id+"-cancel span.text").text("Close");
  $('#'+dialog_id+"-dialog").modal('show');
}

function handle_ajax_form(form_options) {
  // Check for form_options
  form_options = check_form_options(form_options);
  // Get form
  $.get(form_options.action, function(data) {
    // Set header
    if(form_options.title !== null) {
      $('#'+form_options.dialog_id+"-header h5.modal-title").text(form_options.title);
      $('#'+form_options.dialog_id+"-header").show();
    } else {
      $('#'+form_options.dialog_id+"-header").hide();
    }

    // Write form in dialog div
    store_form($('#'+form_options.dialog_id+"-content"), data, form_options.form_id);
    if(form_options.post_load_action) {
      form_options.post_load_action();
    }

    // Set button text and icons
    $('#'+form_options.dialog_id+'-submit span.text').text(form_options.submit);
    if(form_options.submiticon !== null) {
      $('#'+form_options.dialog_id+'-submit span.icon i').removeClass();
      $('#'+form_options.dialog_id+'-submit span.icon i').addClass('fas fa-'+form_options.submiticon);
    }
    $('#'+form_options.dialog_id+'-cancel span.text').text(form_options.cancel);
    if(form_options.submiticon !== null) {
      $('#'+form_options.dialog_id+'-cancel span.icon i').removeClass();
      $('#'+form_options.dialog_id+'-cancel span.icon i').addClass('fas fa-'+form_options.cancelicon);
    }

    // Set button callback functions
    $('#'+form_options.dialog_id+'-submit').off('click').click(function() {
      // Try to post form
      console.log("Posting form to " + form_options.action);
      $.ajax({
        type: "POST",
        url: form_options.action,
        data: $('#'+form_options.form_id).serialize(), // Serializes the form's elements.
        success: function(data) {
          // Success. Reponse: 200
          if(typeof data == 'string') {
            // The form bounced back with some errors
            store_form($('#'+form_options.dialog_id+'-content'), data, form_options.form_id);
            if(form_options.post_load_action) {
              form_options.post_load_action();
            }
            return;
          } else if(typeof data == 'object') {
            // JSON response
            if(data.hasOwnProperty('status') && data.status == 'ok') {
              // Close dialog
              $('#'+form_options.dialog_id+'-dialog').modal('hide');
              // Run successful action
              form_options.success_action(data);
              return;
            }
          }
          // Error
          if(data.hasOwnProperty('message')) {
            message = data.message;
          } else {
            message = 'Generic error. This may indicate a bug. Contact administrator';
          }
          fail_message_dialog(form_options.dialog_id, message);
        },
      }).fail(function(xhr) {
        // POST failed
        data = JSON.parse(xhr.responseText);
        fail_message_dialog(form_options.dialog_id, data.message);
      });
    }).show();
    $('#'+form_options.dialog_id+'-cancel').off('click').click(function() {
      $('#'+form_options.dialog_id+'-dialog').modal('hide');
    });

    // Show dialog
    $('#'+form_options.dialog_id+'-dialog').modal('show');

  }).fail(function(xhr) {
    // GET failed
    data = JSON.parse(xhr.responseText);
    fail_message_dialog(form_options.dialog_id, data.message);
  });
}