(function($) {
  $(document).ready(function() {
    $('.account-widget').each(function() {
      var that = $(this),
        hiddenInput = that.find('.vAccountRawIdWidget'),
        thumbnail = that.find('.thumbnail'),
        description = that.find('.description'),
        clearBtn = that.find('.clear');

      clearBtn.on('click', function() {
        var el = $(this);
        el.hide();
        hiddenInput.val('');
        hiddenInput.trigger('change');
        thumbnail.attr('src', el.data('icon'));
        description.html(el.data('description'));
      });

      var _dismissRelatedLookupPopup = window.dismissRelatedLookupPopup;

      window.dismissRelatedLookupPopup = function(win, chosenId) {
        var name = windowname_to_id(win.name),
          el = $('#' + name);

        if (!el.hasClass('vAccountRawIdWidget')) {
          _dismissRelatedLookupPopup(win, chosenId);
        } else {
          var oldValue = el.val();
          el.val(chosenId);
          win.close();

          if (oldValue != chosenId) {
            var url = that.data('ajaxurl').replace('_id_', chosenId);
            $.getJSON(url, function(data) {
              el.data('account', data);
              if (data.hasOwnProperty('avatar_url')) {
                thumbnail.attr('src', data['avatar_url']);
              }
              description.html(data['provider_name'] + ' &mdash; ' + data['account']);
              clearBtn.show();
            }).error(function() {
              alert('Sorry, something unexpected has happened. Please reload this page and try again.');
            }).done(function() {
              el.trigger('change');
            });
          }
        }
      };
    });
  });
})(django.jQuery);
