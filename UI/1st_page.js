var $messages = $(".messages-content"),
  d,
  h,
  m,
  i = 0;

$(window).on("load", function () {
  setTimeout(function () {
    fakeMessage();
  }, 100);
});

function updateScrollbar() {
  $messages.scrollTop($messages[0].scrollHeight);
}

function setDate() {
  d = new Date();
  if (m != d.getMinutes()) {
    m = d.getMinutes();
    $('<div class="timestamp">' + d.getHours() + ":" + m + "</div>").appendTo(
      $(".message:last")
    );
  }
}

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

var fakeMessages = [
  "Hi there! How can I help you with insurance today?",
  "Are you looking for a specific type of insurance?",
  "Please provide your details, and I'll assist you with the best insurance options.",
  "We offer various insurance policies. Which one are you interested in?"
];

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