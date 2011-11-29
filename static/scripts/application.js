/*
                      _      _                             
__      ___    _ _ __| | __ | |__   __ _ _ __  _ __  _   _ 
\ \ /\ / / |  | | '__| |/ / | '_ \ / _` | '_ \| '_ \| | | |
 \ V  V /| \__/ | |  |   <  | | | | (_| | |_) | |_) | |_| |
  \_/\_/  \____/|_|  |_|\_\ |_| |_|\__,_| .__/| .__/ \__, |
                                       |_|   |_|    |___/ 
*/

function getCookie(name) {
	var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
	return c ? c[1] : undefined;
}


$(document).ready(function() {
	// Find tab classes and activate flippers
	$('.tab').click(function () {
		// Get current elt's class, find corresponding container class
		// and adjust visibility. Set current class to current.
		var $button = $(this);
		
		if (!$button.hasClass('current')) {
			var id = $button.attr('id').match(/(\w+)-button/);
			
			if (id && id[1]) {
				$('.tab.current').toggleClass('current');
				$button.toggleClass('current');
				$('#content .tab-content').hide();
				$('#' + id[1] + '-container').show();
			}
		}
		
		return false;
	});
	
	$('.observed').change(function() {
		var $this = $(this);
		console.log($this.attr('id'));
		var id = $this.attr('id').match(/^([^\-]+).*$/);
		
		if (id.hasOwnProperty(1)) {
			// ugh.
		}
		
		console.log(id);
		//$($this.attr('id')
	});
	
	$("input#client-suggest").autoSuggest("/user/me/contacts.json", {
		selectedItemProp: "fullName",
		selectedValuesProp: "id",
		inputName: "clientID",
		searchObjProps: "name,email",
		startText: "",
		resultsHighlight: false,
		neverSubmit: true,
		selectionLimit: 1,
		preFill: [slug['preFill']],
		
		// See if we can't muck around with internals here and add an email
		// address to the internal data structure if that's what is typed, 
		// and set the data object accordingly... We can handle the hidden 
		// input based on the data, e.g.
		// {"id": null, "name": "joe@example.org", "email": "joe@example.org"}
		
		retrieveComplete: function(data) {
			return data.contacts;
		},
		selectionAdded: function(elem, data) {
			$('.as-results').append('<input type="hidden" id="wh-'+elem.attr('id')+'" name="clientID" value="'+data.id+'" />');
		},
		selectionDeleted: function(elem) {
			$('#wh-'+elem.attr('id')).remove();
		}
	});
	
	$(".js-replace-action").ajaxForm({
		data: {'_xsrf': slug['_xsrf']},
		beforeSubmit: function (arr, $form, options) {
			// @todo: This should only append if it's not already there.
			// We add the .json extension to the form action URL
			// for AJAX requests.
			options.url = $form.attr('action') + '.json';
			options.dataType = "json";
			
			if ($form.attr('id')) {
				// Set the success action based on the form's ID field,
				// if there is one
				options.success = successActions[$form.attr('id')];
			}
			
			if ($form.attr('method') === 'DELETE') {
				// Tornado ignores the HTTP body on DELETE requests, so we
				// need to pack up the form parameters into the query string
				options.url += '?' + jQuery.param(options.data);
				options.data = null;
			}
		}
	});
	
	if (buttonMaps) {
		for (var i = 0, len = buttonMaps.length; i < len; i++) {
			if (buttonMaps.hasOwnProperty(i)) {
				var map = buttonMaps[i];
				
				$("#" + map['id']).click(function(m) {
					// Doing a function application on a closure here
					// to bind the click function to the proper value
					// from the iteration over buttonMaps.
					
					var captureAndSend = function() {
						var data = m['params'], capture = '';
						data._xsrf = getCookie("_xsrf");
						var string = jQuery.param(data);
						
						if (m['capture-id']) {
							var capture = $('#' + m['capture-id']).serialize(data);
							console.log(capture);
						}

						$.ajax({
							url: m['action'],
							data: [jQuery.param(data), capture].join('&'),
							dataType: "text",
							type: m['method'],
							success: successActions[m['id']],
							error: function (jqXHR, textStatus, errorThrown) {
								error = jQuery.parseJSON(jqXHR.responseText);
								alert(error ? error.display : 'There was a problem of some sort');
							}
						});
					};
					
					return function() {
						if (m['html']) {
							console.log('Rendering HTML');
							// Render the included HTML popup and then submit.
							var popup = $(m['html']);
							popup.children('#password-form').submit(function() {
								console.log('clicked');
								captureAndSend();
								return false;
							});
							$('#content').prepend(popup);
						} else {
							captureAndSend();
						}
						return false;
					}
				}(map));
			}
		}
	}
});

successActions = {
	'action-send': function (data, status, xhr) {
		$('.action-button').hide();
		alert('Successfully sent estimate');
	},
	'action-edit': function (data, status, xhr) {
		$('.action-button').hide();
		alert('Successfully edited estimate');
	},
	'action-accept': function (data, status, xhr) {
		$('.action-button').hide();
		alert('Successfully accepted estimate');
	},
	'action-decline': function (data, status, xhr) {
		$('.action-button').hide();
		alert('Successfully declined estimate');
	},
	'action-markcomplete': function (data, status, xhr) {
		$('.action-button').hide();
		alert('Successfully marked the work outlined in this agreement as complete');
	},
	'action-dispute': function (data, status, xhr) {
		$('.action-button').hide();
		alert('Successfully disputed the work completed');
	},
	'action-verify': function (data, status, xhr) {
		$('.action-button').hide();
		$('#password-div').remove();
		alert('Successfully verified the work completed');
	},
	profile_update: function (data, status, xhr) {
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
}

