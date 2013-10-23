
    $(function() {
      var conn = null;

      function log(msg) {
        var control = $('#log');
        control.html(control.html() + msg + '<br/>');
        control.scrollTop(control.scrollTop() + 1000);
      }

      function connect() {
        disconnect();

        var transports = $('#protocols input:checked').map(function(){
            return $(this).attr('id');
        }).get();

        conn = new SockJS('http://' + window.location.host + '/ws', transports);

        log('Connecting...');
      }

    });
