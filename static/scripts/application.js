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

var getQueryArg = (function () {
	var query = window.location.search.substring(1),
		vars = query.split("&"),
		args = {};
	
	for (var i = 0, len = vars.length; i < len; i++) {
		var pair = vars[i].split("=");
		args[pair[0]] = unescape(pair[1]);
	}
	
	return function (name) {
		return args[name];
	}
}());


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
	
	// Limit input length for 'limited-length' fields
	
	$('.limited-length').each(function (idx, elt) {
		var $elt = $(elt),	
			maxLength = Number($elt.attr('data-max-length'), 10),
			$charCount = $(
				'<p class="small" style="font-size:11px;color:#999;margin-bottom:0;text-align:right;"><span class="countdown">' +
				(maxLength - $elt.val().length) + 
				'</span> <span class="text">characters remaining</span></p>'
			);
		
		$charCount.attr('id', $elt.attr('name'));
		$elt.after($charCount);
		var changeFn = function(evt) {
			var currentLength = maxLength - $elt.val().length;
			$count = $elt.siblings('#' + $elt.attr('name'));
			
			if (currentLength <= 10) {
				$count.css('color', 'red');
			} else {
				$count.css('color', '');
			}

			if (currentLength >= 0) {
				$count.find('span.countdown').html(currentLength);
				$count.find('span.text').html('characters remaining');
			} else {
				$count.find('span.countdown').html(- currentLength);
				$count.find('span.text').html('characters over');
			}
		};

		$elt.bind('keyup cut paste', changeFn);
	});

	$('#mode-toggle').buttonset();
	$('#mode-toggle input[name=feedback-mode]').change(function(evt) {
		var selected = $(evt.target).attr('id');
		if (selected === 'contact-help') {
			$('#help-view').slideDown(200);
			$('#feedback-view').slideUp(200);
		} else if (selected === 'contact-feedback') {
			$('#feedback-view').slideDown(200);
			$('#help-view').slideUp(200);
		}
	});

	$('#contact-close').button();
	$('#contact-close').click(function(evt) {
		$('#contact-view').fadeOut(300);
		return evt.preventDefault();
	});

	$('#contact-submit').button();
	$('#contact-submit').click(function(evt) {
		return evt.preventDefault();
	});

	$('#feedback-button').button();
	$('#feedback-button').click(function(evt) {
		$('#contact-view').fadeToggle(300);
		return evt.preventDefault();
	});
	// Revert to jQuery placeholders if Modernizr doesn't detect HTML5 features

	if (!Modernizr.input.placeholder) {
		$("input").each(function() {
			if ($(this).val()=="" && $(this).attr("placeholder")!="") {
				$(this).val($(this).attr("placeholder"));
				$(this).focus(function() {
					if ($(this).val()==$(this).attr("placeholder")) {
						$(this).val("");
					}
				});
				$(this).blur(function() {
					if ($(this).val()=="") {
						$(this).val($(this).attr("placeholder"));
					}
				});
			}
		});
	}

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
		// {"id": null, "fullName": "joe@example.org", "email": "joe@example.org"}
		
		retrieveComplete: function(data) {
			return data.contacts;
		},
		selectionAdded: function(elem, data) {
			// Figure out how to specify what the user ID attribute is named in the hidden field
			// for the create agreement page it's "clientID", but it needs to be "vendorID" for
			// the request agreement form
			
			$('input[name=title]').focus(); //added by marcus to fix next box focus
			$('ul.as-selections li.as-original input').hide(); // added by marcus to fix additional selections problem
		},
		tabPressed: function(elem) {
			// I wish I knew why I have to use a timeout here, but at least it works.
			
			// setTimeout(function() {
			// 	$('input[name=title]').focus();
			// }, 50);
		}
	});
	
	$(".js-replace-action").ajaxForm({
		data: {'_xsrf': slug['_xsrf']},
		beforeSubmit: function (arr, $form, options) {
			// We add the .json extension to the form action URL
			// for AJAX requests.
			
			var action = $form.attr('action');
			options.url = action + (action.match(/\.json$/) ? '' : '.json');
			options.dataType = "json";

			if ($form.attr('id')) {
				// Set the success action based on the form's ID field,
				// if there is one
				options.success = buttonActions[$form.attr('id')];
			}
			
			if ($form.attr('method') === 'DELETE') {
				// Tornado ignores the HTTP body on DELETE requests, so we
				// need to pack up the form parameters into the query string
				options.url += '?' + jQuery.param(options.data);
				options.data = null;
			}
		}
	});
	
	// Hook up button handlers to each element with the appropriate class
	$('.js-button').each(function (idx, elt) {
		var btn = new Button(elt);
	});
	
	$('.js-form').each(function (idx, elt) {
		var form = new JSONForm(elt);
	});
});



var debug = {
	form: function($form) {
		console.log($form.serialize());
	}
};

var Button = function(elt) {
	var self = this;
	
	this.state = 'default';
	this.$elt = $(elt);
	
	this.actions = buttonActions[this.$elt.attr('id')];
	
	var wrapped, clickFn = function(evt) {
		return self.actions[self.state](self, evt);
	};
	
	if (this.$elt.hasClass('cookie-authenticated')) {
		wrapped = function(evt) {
			if (getCookie("auth_timestamp")) {
				return clickFn(evt);
			} else {
				if (!self.hasOwnProperty('$pwPopup')) {
					self.$pwPopup = $('#password-div').clone();
					var btn = new Button(self.$pwPopup.find('.js-button'));
				}
				
				self.$pwPopup.find('#password-form').submit(function(submitEvt, elem) {
					var capture = self.serialize('password-form');
					
					$.ajax({
						url: '/login.json',
						data: capture,
						dataType: 'json',
						type: 'POST',
						success: function (data, status, xhr) {
							self.$pwPopup.slideUp(300);
							clickFn(evt);
						},
						error: self.errorHandler
					});
					
					return submitEvt.preventDefault();
				});
				
				$('#content').prepend(self.$pwPopup);
				self.$pwPopup.slideDown(300);
				return evt.preventDefault();
			}
		};
	} else {
		wrapped = clickFn;
	}
	
	this.$elt.click(wrapped);
};

Button.prototype.collapseButtons = function () {
	$('.action-button li').slideUp(300);
};

Button.prototype.errorHandler = function (jqXHR, textStatus, errorThrown) {
	var error = jQuery.parseJSON(jqXHR.responseText);
	alert(error ? error.display : 'There was a problem of some sort');
};

Button.prototype.serialize = function(captureID, data) {
	var data = data || { };
	data._xsrf = getCookie("_xsrf");
	var capture = jQuery.param(data);
	
	if (captureID) {
		capture += '&' + $('#' + captureID).serialize();
	}
	
	return capture;
};

Button.prototype.jsonHTTPRequest = function(url, method, data, success, error) {
	$.ajax({
		url: url,
		data: data,
		dataType: "json",
		type: method,
		success: success,
		error: error
	});
};



var JSONForm = function(elt) {
	var name,
		self = this;
	
	this.$elt = $(elt);
	this.state = 'default';
	
	name = /(.*)_form/.exec(this.$elt.attr('id'));
	
	if (name && name[1]) {
		this.actions = buttonActions[name[1]];

		this.$elt.submit(function(evt) {
			return self.actions[self.state](self, evt);
		});
	}
};



JSONForm.prototype.serialize = function(captureID, data) {
	var data = data || { };
	data._xsrf = getCookie("_xsrf");
	var capture = jQuery.param(data);
	
	if (captureID) {
		capture += '&' + $('#' + captureID).serialize();
	}
	
	return capture;
};



var Popup = function (parent) {
	var self = this;
	var $container = null;
	
	if (arguments[1]) {
		$container = arguments[1];
	} else {
		$container = $(
		'<div class="clear prompt-box" id="popup-div" style="display:none;">\
			<div class="column-three-fourth">\
				<h3><span style="font-size: 30px; margin-right: 10px;"><a href="#" class="js-close-btn" style="color:#EEE; text-shadow: 1px 1px #333">&#x2297;</a></span> <span id="popup-label"></span></h3>\
			</div>\
			<div class="column-one-fourth">\
			</div>\
		</div>');
	}
	
	this.state = 'closed';
	this.$elt = $container; 
	$(parent).prepend(this.$elt);
	
	this.$elt.find('.js-close-btn').click(function(evt) {
		self.$elt.slideUp(300);
		return evt.preventDefault();
	});
};

Popup.prototype.setLabel = function(label) {
	this.$elt.find('#popup-label').html(label);
	return this;
};

Popup.prototype.open = function() {
	if (this.state == 'open') {
		return this;
	}
	
	this.$elt.slideDown(300);
	this.state = 'closed';
	return this;
};

Popup.prototype.close = function() {
	if (this.state == 'closed') {
		return this;
	}
	
	this.$elt.slideUp(300);
	this.state = 'open';
	return this;
};

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

$('.notes.toggle').click(function(e) {
	var $textArea = $(this).children('textarea');
	if (!$(e.target).is('textarea') && ($textArea.is(':hidden') || $textArea.val() === '')) {
		$(this).children('textarea').toggle();
	};
});

