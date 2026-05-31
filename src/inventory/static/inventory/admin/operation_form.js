// Defer until DOM and Django admin scripts (including jQuery) are ready.
document.addEventListener('DOMContentLoaded', function () {
  var $ = django.jQuery;
  var $responsible = $('#id_responsible');
  var $location = $('#id_location');
  if (!$responsible.length || !$location.length) return;

  // When responsible changes, clear the location selection so the user
  // cannot keep a value that belongs to the previous responsible.
  // DAL's forward mechanism will re-fetch filtered options automatically.
  $responsible.on('change', function () {
    $location.empty().trigger('change');
  });
});
