/*
                      _      _                             
__      _()    ()_ __| | __ | |__   __ _ _ __  _ __  _   _ 
\ \ /\ / /-    -| '__| |/ / | '_ \ / _` | '_ \| '_ \| | | |
 \ V  V /| \__/ | |  |   <  | | | | (_| | |_) | |_) | |_| |
  \_/\_/  \____/|_|  |_|\_\ |_| |_|\__,_| .__/| .__/ \__, |
                                       |_|   |_|    |___/ 
*/

function getCookie(name) {
	var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
	return c ? c[1] : undefined;
}

// jQuery.postJSON = function(url, data, callback) {
// 	data._xsrf = getCookie("_xsrf");
// 	console.log(data);
// 	$.ajax({
// 		url: url,
// 		data: $.param(data),
// 		contentType: false,
// 		processData: false,
// 		//dataType: "text",
// 		type: "POST",
// 		success: callback,
// 		beforeSend: function (jqXHR, settings) {
// 			console.log(jqXHR);
// 			return false;
// 		}
// 	});
// };
// 
// 
// $.fn.submitAJAX = function(callback) {
// 	var $form = this, params = $form.serializeArray();
// 	//TODO: look into FormData object.
// 	// Can use jQuery.each($('input[type=file]')[0].files, function (i, file) { data.append('photo', file); });
// 	$.postJSON($form.attr('action') + '.json', params, callback);
// };

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
		beforeSubmit: function (arr, $form, options) {
			options.url = $form.attr('action') + '.json';
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
					
					return function() {
						var data = m['params'], capture = '';
						data._xsrf = getCookie("_xsrf");
						var string = jQuery.param(data);
						
						if (m['capture-id']) {
							capture = $('#' + m['capture-id']).serialize(data);
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
		alert('Successfully verified the work completed');
	}
}

