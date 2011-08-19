/*
                     _      _                             
__      ___   _ _ __| | __ | |__   __ _ _ __  _ __  _   _ 
\ \ /\ / / | | | '__| |/ / | '_ \ / _` | '_ \| '_ \| | | |
 \ V  V /| |_| | |  |   <  | | | | (_| | |_) | |_) | |_| |
  \_/\_/  \__,_|_|  |_|\_\ |_| |_|\__,_| .__/| .__/ \__, |
                                       |_|   |_|    |___/ 
*/

function getCookie(name) {
	var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
	return c ? c[1] : undefined;
}

jQuery.postJSON = function(url, data, callback) {
	data._xsrf = getCookie("_xsrf");
	$.ajax({
		url: url,
		data: $.param(data),
		dataType: "text",
		type: "POST",
		success: callback
	});
};


$.fn.submitAJAX = function(callback) {
	var $form = this, params = $form.serializeArray();
	$.postJSON($form.attr('action') + '.json', params, callback);
};

$(document).ready(function() {
	$("input#client-suggest").autoSuggest("/user/me/contacts.json", {
		selectedItemProp: "name",
		selectedValuesProp: "id",
		inputName: "clientID",
		searchObjProps: "name,email",
		startText: "Email Address or Name of Existing Contact",
		resultsHighlight: false,
		neverSubmit: true,
		selectionLimit: 1,
		
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
	
	
	$("#confirm-edit-button").click(function() {
		$("form").submitAJAX(function(data, status, xhr) {
			//console.log(xhr.getResponseHeader('Location'));
			//console.log(data);
		});
		return false;
	});
	
	for (var i = 0, len = buttonMaps.length; i < len; i++) {
		if (buttonMaps.hasOwnProperty(i)) {
			var map = buttonMaps[i];
			$("#" + map['id']).click(function(m) {
				return function() {
					var data = m['params'];
					data._xsrf = getCookie("_xsrf");
					$.ajax({
						url: m['action'],
						data: $.param(data),
						dataType: "text",
						type: m['method'],
						success: function(data, status, xhr) {
							console.log(data);
						}
					});
					return false;
				}
			}(map));
		}
	}
});

