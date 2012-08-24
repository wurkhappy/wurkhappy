var buttonActions = {
	'password-submit': {
		default: function (self, evt) {
			$('#password-form').submit();
			return evt.preventDefault();
		}
	},
	
	'request-send': {
		default: function (self, evt) {
			var capture = self.serialize('request-form');
			
			var popup = new Popup('#content');
			
			$.ajax({
				url: '/agreement/request.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Your agreement request has been sent. You can either request another agreement, or go <a href="/">home</a>.').open();
					// Only disable the button until the form has been modified
					$('#request-form ul li.as-selection-item').remove();
					$('#request-form input[type=hidden]').remove();
					$('#request-form textarea#message').val('');
					$('#action-save').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	}
};