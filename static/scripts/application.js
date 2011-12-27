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
	// Activate registered actions
	for (var i = 0, len = actions.length; i < len; i++) {
		if (actions.hasOwnProperty(i)) {
			actions[i]();
		}
	}
	
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
	
	$("input#client-suggest").autoSuggest("/user/me/contacts.json", {
		selectedItemProp: "fullName",
		selectedValuesProp: "id",
		inputName: slug['autosuggestCapture'], //"clientID",
		searchObjProps: "fullName,email",
		startText: "",
		resultsHighlight: false,
		neverSubmit: true,
		selectionLimit: 1,
		preFill: slug['preFill'],
		
		// See if we can't muck around with internals here and add an email
		// address to the internal data structure if that's what is typed, 
		// and set the data object accordingly... We can handle the hidden 
		// input based on the data, e.g.
		// {"id": null, "name": "joe@example.org", "email": "joe@example.org"}
		
		retrieveComplete: function(data) {
			return data.contacts;
		},
		selectionAdded: function(elem, data) {
			// Figure out how to specify what the user ID attribute is named in the hidden field
			// for the create agreement page it's "clientID", but it needs to be "vendorID" for
			// the request agreement form
			if (data['id'] === "") {
				$('.as-results').append('<input type="hidden" id="wh-'+elem.attr('id')+'" name="email" value="'+data.fullName+'" />');
			} else {
				$('.as-results').append('<input type="hidden" id="wh-'+elem.attr('id')+'" name="'+slug['autosuggestCapture']+'" value="'+data.id+'" />');
			}
		},
		selectionRemoved: function(elem) {
			elem.remove();
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
					
					var captureAndSend = function(evt) {
						var data = m['params'], capture = '';
						data._xsrf = getCookie("_xsrf");
						var string = jQuery.param(data);
						
						if (m['capture-id']) {
							var capture = $('#' + m['capture-id']).serialize(data);
							console.log(capture);
						}

						var commentLength = formValidator.checkCommentLength($('textarea'));
						if (m['id'] === 'action-accept' && commentLength > 0) {
							alert('By accepting the estimate, no additional comments are allowed so your notes will not be sent-- save them while you can!');
							return false;
						} else if (m['id'] === 'action-decline' && commentLength < 10) {
							alert('Please add a few comments (reasons for declining, questions, etc.) regarding the estimate.');
							return false;
						} else if (m['id'] === 'action-dispute' && commentLength < 5) {
							alert('Please add a few comments explaining why you think the work has not been completed.');
							return false;
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
						return evt.preventDefault();
					};
					
					if (m['html']) {
						var $popup = $(m['html']);
						$popup.find('#verify-amount').html(slug['currentPhase']['amount']);
						$popup.find('#verify-account').html(slug['account']);
						
						var action = function(evt) {
							// Render the included HTML popup and then submit.
							var $button = $(evt.target);
							$button.unbind();
							$button.addClass('cancel');
							$button.html('Cancel');

							$button.click(function (evt) {
								$popup.slideUp(300);
								var $button = $(evt.target);
								$button.unbind();
								$button.removeClass('cancel');
								$button.html(m['name']);
								$button.click(action);
								return evt.preventDefault();
							});
							
							$popup.children('#password-form').submit(captureAndSend);
							
							$('#content').prepend($popup);
							$popup.slideDown(300);
							return evt.preventDefault();
						};
						return action;
					} else {
						return captureAndSend;
					}
				}(map));
			}
		}
	}
});



// var wh = { };
// 
// wh.autoSuggest = {
// 	// AutoSuggest boxes need some prep work before they'll work. We need to
// 	// specify a data source, a selected item name, <<and some other shit.>>
// 	
// 	// wh.autoSuggest.init(
// 	// 	'/path/to/data',
// 	// 	'selectionName', ...
// 	// )($('selected-items'));
// 	
// 	/* 
// 	dataSource = {
// 		url: "/user/me/contacts.json",
// 		indexPath: "contacts",
// 		searchProperties: ['fullName', 'email'],
// 		tokenDisplayProperty: "fullName",
// 		tokenValueProperty: "id",
// 		unmatchedTokenValueProperty: "email",
// 		defaultTokens: slug['defaultTokens']
// 	}
// 	*/
// 	init: function (dataSource, inputName) {
// 		var defaults = this.pluginDefaults;
// 		defaults.inputName = inputName;
// 		defaults.
// 		
// 		return function ($element) {
// 			$element.autoSuggest(dataSource, defaults);
// 		}
// 	},
// 	
// 	createDefaults: function () {
// 		var inputName = null;
// 		return {
// 			selectedItemProp: "fullName",
// 			selectedValuesProp: "id",
// 			inputName: inputName, // Override in init()
// 			searchObjProps: "fullName,email",
// 			startText: "",
// 			resultsHighlight: false,
// 			neverSubmit: true,
// 			selectionLimit: 1,
// 			preFill: slug['preFill'],
// 		
// 			// See if we can't muck around with internals here and add an email
// 			// address to the internal data structure if that's what is typed, 
// 			// and set the data object accordingly... We can handle the hidden 
// 			// input based on the data, e.g.
// 			// {"id": null, "name": "joe@example.org", "email": "joe@example.org"}
// 		
// 			retrieveComplete: function(data) {
// 				return data.contacts;
// 			},
// 		
// 			selectionAdded: function(elem, data) {
// 				// Figure out how to specify what the user ID attribute is named in the hidden field
// 				// for the create agreement page it's "clientID", but it needs to be "vendorID" for
// 				// the request agreement form
// 				if (data['id'] === "") {
// 					$('.as-results').append('<input type="hidden" id="wh-'+elem.attr('id')+'" name="email" value="'+data.fullName+'" />');
// 				} else {
// 					$('.as-results').append('<input type="hidden" id="wh-'+elem.attr('id')+'" name="clientID" value="'+data.id+'" />');
// 				}
// 			};
// 		},
// 		
// 		selectionRemoved: function(elem) {
// 			elem.remove();
// 			$('#wh-'+elem.attr('id')).remove();
// 		}
// 	}
// };


var formValidator = {
	checkCommentLength: function(commentFields) {
		var commentsLength = 0;
		for(var i=0, len=commentFields.length; i < len; i++) {
			var comment = $(commentFields[i]).val();
			commentsLength += comment.length;
		}
		return commentsLength;
	}
};


successActions = {
	'action-save': function (data, status, xhr) {
		alert('Your changes have been saved');
		$('#action-save').slideUp(300);
	},
	'action-send': function (data, status, xhr) {
		alert('Successfully sent estimate');
		$('.action-button li').slideUp(300);
	},
	'action-resend': function (data, status, xhr) {
		alert('Successfully sent estimate');
		$('.action-button li').slideUp(300);
	},
	'action-edit': function (data, status, xhr) {
		alert('Successfully edited estimate');
		$('.action-button li').slideUp(300);
	},
	'action-accept': function (data, status, xhr) {
		alert('Successfully accepted estimate');
		$('.action-button li').slideUp(300);
	},
	'action-decline': function (data, status, xhr) {
		alert('Your request for changes has been sent');
		$('.action-button li').slideUp(300);
	},
	'action-markcomplete': function (data, status, xhr) {
		alert('The work outlined in the current phase has been marked complete');
		$('.action-button li').slideUp(300);
	},
	'action-dispute': function (data, status, xhr) {
		alert('Successfully disputed the work completed');
		$('.action-button li').slideUp(300);
	},
	'action-verify': function (data, status, xhr) {
		alert('Successfully verified the work completed');
		$('.action-button li').slideUp(300);
		$('#password-div').slideUp(300);
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

$('.notes.toggle').click(function(e) {
	if (!$(e.target).is('textarea')) {
		$(this).children().toggle();
		$(this).removeClass('toggle').unbind();
	};
});

