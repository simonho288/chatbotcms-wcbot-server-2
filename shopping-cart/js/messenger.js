// Messenger Extension
(function (d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) { return; }
  js = d.createElement(s); js.id = id;
  js.src = "//connect.facebook.com/en_US/messenger.Extensions.js";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'Messenger'));
window.extAsyncInit = function () {
  MessengerExtensions.getUserID(function success(uids) {
    console.log(uids);
    var psid = uids.psid;
  }, function error(err, errorMessage) {
    console.log(errorMessage);
  });
}
