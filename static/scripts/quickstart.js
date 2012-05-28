
var wurkHappy = {
	User: function (properties) {
		this.id = properties['id'];
		this.firstName = properties['firstName'];
		this.lastName = properties['lastName'];
		this.fullName = properties['fullName'];
		this.email = properties['email'];
		this.profileURL = properties['profileURL'];
		this.telephone = properties['telephone'];
	}
}

var buttonActions = {
	
	'set-pw': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			var bodyString = self.serialize('set-pw_form');
			
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
					$('#set-pw_form input[type=password]').val('');
				}
			});
			
			return evt.preventDefault();
		}
	},
	
	'login': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			var bodyString = self.serialize('login_form');
			
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
					error.display = error.display.replace("email and password combination", "password").replace("any of", "");
					popup.setLabel(error ? error.display : 'Your password was incorrect.').open();
					$('#login_form input[type=password]').val('');
				}
			});
			
			return evt.preventDefault();
		}
	},
	
	'profile-edit': {
		default: function (self, evt) {
			var agree = $('form#profile-edit_form input#agree').attr('checked');
			
			if (agree) {
				// Do AJAX form.
				// TODO: Note that we're not specifying success and error functions here and we should.
				// Also, the success function should update the current_user property.
				$('form#profile-edit_form').submit();
			
				$('#details-container').slideUp(300).fadeOut(300);
				$('#dwolla-container').slideDown(300).fadeIn(300);
			} else {
				var popup = new Popup('#content');
				popup.setLabel("You must agree to the Wurk Happy Terms of Use to continue.").open();
			}
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
			window.location = 'https://www.dwolla.com/register';
			return evt.preventDefault();
			// $('#dwolla-submit_form input#email').val(wurkHappy.current_user['email']);
			// $('#dwolla-submit_form input#firstName').val(wurkHappy.current_user['firstName']);
			// $('#dwolla-submit_form input#lastName').val(wurkHappy.current_user['lastName']);
			// $('#dwolla-submit_form input#phone').val(wurkHappy.current_user['telephone']);
			// 
			// $('#dwolla-container').slideUp(300).fadeOut(300);
			// $('#dwolla-create-container').slideDown(300).fadeIn(300);
			// 
			// return evt.preventDefault();
		}
	},
	
	'dwolla-submit': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			var bodyString = self.serialize('dwolla-submit_form');
			
			$.ajax({
				url: '/login.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					// self.state = 'disabled';
					// $(evt.target).addClass('disabled');
					// 
					// $('#password-form input').val('');
					// 
					// wurkHappy.current_user = new wurkHappy.User(data['user']);
					// 
					// $('#password-container').slideUp(300).fadeOut(300);
					// $('#details-container').slideDown(300).fadeIn(300);
				},
				error: function (jqXHR, textStatus, errorThrown) {
					// var error = jQuery.parseJSON(jqXHR.responseText);
					// error.display = error.display.replace("email and password combination", "password").replace("any of", "");
					// popup.setLabel(error ? error.display : 'Your password was incorrect.').open();
					// $('#login_form input[type=password]').val('');
				}
			});
			
			return evt.preventDefault();
		}
	},
	
	'dwolla_skip': {
		default: function (self, evt) {
			window.location = '/';
			return evt.preventDefault();
		}
	},
	
};

actions.push(function () {
	$('#dwolla-account-type').change(function(evt) {
		if ($(evt.target).val() === 'Commercial') {
			$('#dwolla-business-info').slideDown(300).fadeIn(300);
		} else {
			$('#dwolla-business-info').slideUp(300).fadeOut(300);
		}
	});
});