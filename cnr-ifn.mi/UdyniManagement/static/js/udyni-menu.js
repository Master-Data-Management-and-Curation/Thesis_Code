$(document).ready(function() {

  // Get current location
  var current_location = window.location.pathname;

  // Search for all
  var active_location = "";
  var active_object;
  $("#accordionSidebar a.collapse-item").each(function() {
    if($(this).attr('href') != "") {
      //console.log("L:"+current_location+", H:"+$(this).attr('href'));
      if(current_location.startsWith($(this).attr('href'))) {
        // Found location
        if($(this).attr('href').length > active_location.length) {
          active_location = $(this).attr('href');
          active_object = $(this);
        }
      }
    }
  });
  if(active_location.length > 0) {
    active_object.addClass('active');
    active_object.closest("div.collapse").addClass('show');
    active_object.closest("li.nav-item").addClass('active');
  }
});
