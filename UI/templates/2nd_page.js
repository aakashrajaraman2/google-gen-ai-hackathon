
function insertMessage() {
  var msg = $(".message-input").val();
  if ($.trim(msg) === "") {
    return false;
  }
  $('<div class="message message-personal">' + msg + "</div>")
    .appendTo($(".messages-content"))
    .addClass("new");
  setDate();
  $(".message-input").val(null);
  updateScrollbar();
  setTimeout(function () {
    fakeMessage();
  }, 1000 + Math.random() * 20 * 100);
}

$(".message-submit").click(function () {
  insertMessage();
});

$(window).on("keydown", function (e) {
  if (e.which == 13) {
    insertMessage();
    return false;
  }
});


function fakeMessage() {
  if ($(".message-input").val() !== "") {
    return false;
  }
  $('<div class="message loading new"><figure class="avatar"><img src="https://www.pikpng.com/pngl/m/9-95034_bot-eyes-angry-bot-png-clipart.png" alt="avatar"/></figure><span></span></div>')
    .appendTo($(".messages-content"));
  updateScrollbar();

  setTimeout(function () {
    $(".message.loading").remove();
    $('<div class="message new"><figure class="avatar"><img src="https://www.pikpng.com/pngl/m/9-95034_bot-eyes-angry-bot-png-clipart.png" alt="avatar"/></figure>' + fakeMessages[i] + "</div>")
      .appendTo($(".messages-content"))
      .addClass("new");
    setDate();
    updateScrollbar();
    i++;
  }, 1000 + Math.random() * 20 * 100);
}