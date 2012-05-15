
var wurkHappy = {
	User: function (properties) {
		this.id = properties['id'];
		this.fullName = properties['fullName'];
		this.email = properties['email'];
		this.profileURL = properties['profileURL'];
		this.telephone = properties['telephone'];
	}
}

var buttonActions = {
	
	'set-pw-button': {
		default: function (self, evt) {
			var popup = new Popup('#internal');
			var bodyString = self.serialize('password-form');
			
			$.ajax({
				url: '/user/me/password.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					self.state = 'disabled';
					$(evt.target).addClass('disabled');
					
					$('#password-form input').val('');
					
					wurkHappy.current_user = new wurkHappy.User(data['user']);
					
					$('#password-container').slideUp(300).fadeOut(300);
					$('#details-container').slideDown(300).fadeIn(300);
				},
				error: function (jqXHR, textStatus, errorThrown) {
					var error = jQuery.parseJSON(jqXHR.responseText);
					popup.setLabel(error ? error.display : 'There was a problem setting your password.').open();
					$('#password-form input').val('');
				}
			});
			
			return evt.preventDefault();
		}
	},
	
	'login-button': {
		default: function (self, evt) {
			var popup = new Popup('#internal');
			var bodyString = self.serialize('password-form');
			
			$.ajax({
				url: '/login.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					self.state = 'disabled';
					$(evt.target).addClass('disabled');
					
					$('#password-form input').val('');
					
					wurkHappy.current_user = new wurkHappy.User(data['user']);
					
					$('#password-container').slideUp(300).fadeOut(300);
					$('#details-container').slideDown(300).fadeIn(300);
				},
				error: function (jqXHR, textStatus, errorThrown) {
					var error = jQuery.parseJSON(jqXHR.responseText);
					popup.setLabel(error ? error.display : 'Your password was incorrect.').open();
					$('#password-form input').val('');
				}
			});
			
			return evt.preventDefault();
		}
	},
	
	'profile-submit': {
		default: function (self, evt) {
			// Do AJAX form.
			// TODO: Note that we're not specifying success and error functions here and we should.
			$('form#profile-edit').submit();
			
			$('#details-container').slideUp(300).fadeOut(300);
			$('#dwolla-container').slideDown(300).fadeIn(300);
			
			return evt.preventDefault();
		}
	},
	
	'dwolla_connect': {
		default: function (self, evt) {
			var width = window.outerWidth, height = window.outerHeight, x = 0, y = 0;
			
			var $dimmer = $('<div class="dimmer" style="display:none;"></div>');
			$('body').prepend($dimmer);
			$dimmer.fadeIn(300);
			
			var authWindow = window.open(slug['authorizeURL'], 'Permission Request', 'width=602,height=430,resizable=0,toolbar=0,location=0,menubar=0,directories=0');
			
			if (window.hasOwnProperty('screenX') && window.hasOwnProperty('screenY')) {
				x = window.screenX;
				y = window.screenY;
			} else {
				x = window.screenLeft;
				y = window.screenTop;
			}
			
			authWindow.resizeTo(602, 430);
			authWindow.moveTo(x + (width / 2) - 301, y + (height / 2) - 215);
			
			var windowPollTimer;
			windowPollTimer = setInterval(function() {
				if (authWindow && authWindow.closed) {
					clearInterval(windowPollTimer);
					$dimmer.fadeOut(300);
				}
			}, 100);
			
			var successPollTimer;
			successPollTimer = setInterval(function() {
				var token = getQueryArg('t');
				if (token) {
					$.ajax({
						url: '/user/me/account.json',
						data: {'t': token},
						dataType: 'json',
						type: 'GET',
						success: function (data, status, xhr) {
							if (data['dwolla'] === true) {
								clearInterval(successPollTimer);
								window.location = '/';
							}
						}
					});
				}
			}, 800);
			
			return evt.preventDefault();
		}
	},
	
	'dwolla_create': {
		default: function (self, evt) {
			return evt.preventDefault();
		}
	},
	
	'dwolla_skip': {
		default: function (self, evt) {
			window.location = '/';
			return evt.preventDefault();
		}
	},
	
}