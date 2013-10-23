    SolomonPixel = {
      track: function(ext) {
        if(typeof(ext) == "undefined") { ext = {}; }

        // Information about the User
        ext.ctry = geoip_country_name();
        ext.cty = geoip_city();
        ext.hr = document.location.href;
        ext.pn = document.location.pathname;
        ext.ow = window.outerWidth;
        ext.oh = window.outerHeight;

        if(document.referrer && document.referrer != "") {
          ext.ref = document.referrer;
        }

        ext.rnd = Math.floor(Math.random() * 10e12);

        var params = [];
        for(var key in ext) {
          if(ext.hasOwnProperty(key)) {
            params.push(encodeURIComponent(key) + "=" + encodeURIComponent(ext[key]));
          }
        }

        var img = new Image();
            img.clientWidth = 1;
            img.clientHeight = 1;

        //Use the address of Solomon
        img.src = 'http://localhost:8010?' + params.join('&');
      }
    };
