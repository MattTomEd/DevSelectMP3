$(document).ready(function () {
    $('.sidenav').sidenav({
        edge: "right"
    });
});

$('.chips').chips();

$('.chips-placeholder').chips({
    placeholder: 'Enter a skill...',
    secondaryPlaceholder: 'Add another skill...',
});

$(document).ready(function(){
    $('.collapsible').collapsible();
  });