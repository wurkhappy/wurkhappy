
var buttonActions = {
	
	profile_set: function (data, status, xhr) {
		$('#profile-button').click();
	},
	
	password_set: function (data, status, xhr) {
		$('#details-button').click();
	},
	
	profile_update: function (data, status, xhr) {
		// @todo: Manually check the status code
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
		// @todo: Clear the form fields!
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
		// @todo: Clear the form fields!
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