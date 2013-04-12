
var buttonActions = {
	'password-submit': {
		default: function (self, evt) {
			$('#password-form').submit();
			return evt.preventDefault();
		}
	},
	
	user_info_edit: {
		default: function (self, evt) {
			var $profilePreview = $('#profile_info'),
				$profilePhotoUpload = $('#profile_photo_upload'),
				$profileEdit = $('#profile_form'),
				$profileEditButton = $('#user_info_edit_ul'),
				$profileUpload = $('#profile_photo_upload');

			$profileEditButton.hide();
			$profilePreview.hide();
			$profileEdit.show();
			$profileUpload.show();
		}
	},

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
					
					window.location.href = '/';
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
						$('#amazon-container').html(
							'<div class="column-three-fourth">' +
							'<h2>Amazon Marketplace Account</h2>' +
							'<h1 style="color:green;font-size:50px;float:left">&#9745;</h1>' +
							'<p>Your Amazon Marketplace Account has been successfully connected ' +
							'and verified with Amazon. You are ready to start receiving payments ' +
							'through Wurk Happy!</p>' +
							'</div>'
						);
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
	
	profile_update: function (data, status, xhr) {
		// TODO: Manually check the status code
		data.telephone = data.telephone || '';
		var $profilePreview = $('#profile_info'),
			$profileEdit = $('#profile_form'),
			$profileEditButton = $('#user_info_edit_ul'),
			$profileUpload = $('#profile_photo_upload');
		
		$profilePreview.find('img#profile_image').attr('src', data.profileURL[1]);
		$profilePreview.find('a#profile_full_name').html(data.fullName);
		$profilePreview.find('p#profile_email').html(data.email);
		$profilePreview.find('p#profile_telephone').html(data.telephone);
		
		$profileEditButton.show();
		$profilePreview.show();
		$profileEdit.hide();
		$profileUpload.hide();
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
