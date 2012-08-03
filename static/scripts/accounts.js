
var buttonActions = {
	
	profile_set: function (data, status, xhr) {
		$('#profile-button').click();
	},
	
	password_set: function (data, status, xhr) {
		$('#details-button').click();
	},
	
	'password-change': {
		default: function (self, evt) {
			var popup = new Popup('#internal');
			var bodyString = self.serialize('password-form');
			
			$.ajax({
				url: '/user/me/password.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Your password has successfully been changed.').open();
					$('#password-form input').val('');
				},
				error: function (jqXHR, textStatus, errorThrown) {
					var error = jQuery.parseJSON(jqXHR.responseText);
					popup.setLabel(error ? error.display : 'There was a problem changing your password. It has not been changed.').open();
					$('#password-form input').val('');
				}
			});
			
			return evt.preventDefault();
		}
	},
	
	'password-set': {
		default: function (self, evt) {
			var popup = new Popup('#internal');
			var bodyString = self.serialize('password-form');
			
			$.ajax({
				url: '/user/me/password.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Your password has successfully been set.').open();
					
					self.state = 'disabled';
					$(evt.target).addClass('disabled');
					
					$('#password-form input').val('');
					$('#details-button').click();
				},
				error: function (jqXHR, textStatus, errorThrown) {
					var error = jQuery.parseJSON(jqXHR.responseText);
					popup.setLabel(error ? error.display : 'There was a problem setting your password.').open();
					$('#password-form input').val('');
				}
			});
			
			return evt.preventDefault();
		},
		
		disabled: function (self, evt) {
			return evt.preventDefault();
		}
	},
	
	'password-reset': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			var bodyString = self.serialize('password-reset_form');
			
			$.ajax({
				url: '/user/me/password/reset.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('We have successfully received your request, and we&rsquo;ve sent an email with further instructions. Please check your spam folder if you don&rsquo;t see the email.').open();
				},
				error: function (jqXHR, textStatus, errorThrown) {
					var error = jQuery.parseJSON(jqXHR.responseText);
					popup.setLabel(error ? error.display : 'There was a problem communicating with our server. Please try again.').open();
				}
			});
			
			return evt.preventDefault();
		}
	},
	
	'profile-submit': {
		default: function (self, evt) {
			// Do AJAX form.
			$('form#profile-edit').submit();
			
			$('#dwolla-button').click();
			return evt.preventDefault();
		}
	},
	
	'profile-edit': function (data, status, xhr) {
		var popup = new Popup('#internal');
		popup.setLabel('Your profile has been updated.').open();
	},
	
	'amazon_verify': {
		default: function (self, evt) {
			
			var successFunction = function (data, status, xhr) {
				var location = xhr.getResponseHeader('Location');
				
				$.ajax({
					url: location,
					dataType: 'json',
					type: 'GET',
					success: function (data, status, xhr) {
						alert('plz collapse box kthx');
					}
				});
			};
			
			$.ajax({
				url: '/user/me/account/amazonVerificationQueue.json',
				data: {'_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: successFunction
			});
			
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
	
	profile_update: function (data, status, xhr) {
		// TODO: Manually check the status code
		data.telephone = data.telephone || '';
		$('#profile_preview').replaceWith('<div id="profile_preview">\
			<h2>Profile Preview</h2>\
			<div class="data-table">\
				<table border="0" cellspacing="0" cellpadding="0">\
					<tr>\
						<td class="meta">\
							<span><img src="' + data.profileURL[0] + '" alt="Profile photo" width="50" height="50" /></span>\
						</td>\
						<td>\
							<h3><a href="/user/me/profile">' + data.fullName + '</a></h3>\
							<p>' + data.email + '</p>\
							<p>' + data.telephone + '</p>\
						</td>\
					</tr>\
				</table>\
			</div>\
		</div>');
	},
	
	card_update: function (data, status, xhr) {
		// TODO: Clear the form fields!
		$('#stored-card').remove();
		$('#card-container').prepend('<div id="stored-card">\
			<h2>Stored Credit Card</h2>\
			<h3>&bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; ' + data.display + '</h3>\
			<p>Expires ' + data.cardExpires + '</p>\
			<!--<p>Billing ZIP: </p>-->\
			<form action="/user/me/paymentmethod/' + data.id + '" method="DELETE" class="js-replace-action clear">\
				<fieldset class="submit-buttons">\
					<input type="submit" value="Delete This Card" />\
				</fieldsest>\
			</form>\
		</div>');
	},
	
	card_delete: function (data, status, xhr) {
		$('#stored-card').remove();
	},
	
	bank_update: function (data, status, xhr) {
		// TODO: Clear the form fields!
		$('#stored-bank').remove();
		$('#bank-container').prepend('<div id="stored-bank">\
			<h2>Stored Bank Account</h2>\
			<p>Routing Number</p>\
			<h3>&bull;&bull;&bull;&bull;&bull;&bull;' + data.abaDisplay + '</h3>\
			<p>Account Number</p>\
			<h3>&bull;&bull;&bull;&bull; &bull;&bull;' + data.display + '</h3>\
			<form action="/user/me/paymentmethod/' + data.id + '" method="DELETE" class="js-replace-action clear" id="bank_delete">\
				<fieldset class="submit-buttons">\
					<input type="submit" value="Delete This Card" />\
				</fieldsest>\
			</form>\
		</div>');
	},
	
	bank_delete: function (data, status, xhr) {
		$('#stored-bank').remove();
	}
};

var hashHandler = function() {
	if (window.location.hash) {
		var id = window.location.hash.match(/#(\w+)/);
		var $button = $('#' + id[1] + '-button');
		
		if ($button.length) {
			$('.tab.current').toggleClass('current');
			$button.toggleClass('current');
			$('#content .tab-content').hide();
			$('#' + id[1] + '-container').show();
		}
	}
};

window.onhashchange = hashHandler;
actions.push(hashHandler);