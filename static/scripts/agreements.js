
var buttonActions = {
	
	'action-save': {
		default: function (self, evt) {
			// validate..
			// var commentLength = ...
			
			var capture = self.serialize('agreement-form');
			var formAction = $('#agreement-form').attr('action');
			
			var popup = new Popup('#content');
			
			$.ajax({
				url: formAction + '/save.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Your changes have been saved').open();
					// Only disable the button until the form has been modified
					$('#agreement-form').attr('action', '/agreement/' + data.id);
					$('#action-save').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-send': {
		default: function (self, evt) {
			var capture = self.serialize('agreement-form');
			var formAction = $('#agreement-form').attr('action');
			var popup = new Popup('#content');
			
			$.ajax({
				url: formAction + '/send.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Successfully sent estimate').open();
					$('.action-button li').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
    
	'action-resend': {
		default: function (self, evt) {
			var capture = self.serialize('agreement-form');
			var popup = new Popup('#content');
			
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/send.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Successfully sent estimate').open();
					$('.action-button li').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-accept': {
		default: function (self, evt) {
			var commentLength = formValidator.checkCommentLength($('textarea'));
			var popup = new Popup('#content');
			
			if (commentLength > 0) {
				// TODO: Don't allow comments? Figure this out...
				alert('By accepting the estimate, no additional comments are allowed so your notes will not be sent&mdash;save them while you can!');
				return evt.preventDefault();
			}
			
			var capture = self.serialize('comments-form');
			
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/accept.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Successfully accepted estimate').open();
					$('.action-button li').slideUp(300);
					$('.add.notes').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-decline': {
		default: function (self, evt) {
			var commentLength = formValidator.checkCommentLength($('textarea'));
			var popup = new Popup('#content');
			
			if (commentLength < 10) {
				// TODO: Better UI here please, thank you.
				alert('Please add a few comments (reasons for declining, questions, etc.) regarding the estimate.');
				return evt.preventDefault();
			}
			
			var capture = self.serialize('comments-form');
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/decline.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Your request for changes has been sent').open();
					$('.action-button li').slideUp(300);
					$('.add.notes').each(function(index) {
						var $textArea = $(this).children('textarea');
						var content = $textArea.val();
						if (content !== '') {
							$textArea.slideUp(300);
							$(this).children('p').html(content);
						} else {
							$(this).slideUp(300);
						}
					});
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-markcomplete': {
		default: function (self, evt) {
			var bodyString = self.serialize();
			var popup = new Popup('#content');
			
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/mark_complete.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('The work outlined in the current phase has been marked complete').open();
					$('.action-button li').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-dispute': {
		default: function (self, evt) {
			var commentLength = formValidator.checkCommentLength($('textarea'));
			if (commentLength < 5) {
				alert('Please add a few comments explaining why you think the work has not been completed.');
				return evt.preventDefault();
			}
			
			var popup = new Popup('#content');
			var bodyString = self.serialize('comments-form');
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/dispute.json',
				data: bodyString,
				dataType: "json",
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Successfully disputed the work completed').open();
					$('.action-button li').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-request': {
		default: function (self, evt) {
			// validate...
			var popup = new Popup('#content');
			var bodyString = self.serialize('form');
			$.ajax({
				url: '/agreement/request.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Successfully sent your request').open();
					$('.action-button li').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-verify': {
		default: function (self, evt) {
			self.state = 'cancel';
			
			var $button = $(evt.target);
			self.name = $button.html();
			
			if (!self.hasOwnProperty('$popup')) {
				self.$popup = $('#confirmation-div').clone();
				self.$popup.find('#verify-amount').html(slug['currentPhase']['amount']);
			}
			
			// Render the included HTML popup and then submit.
			$button.addClass('cancel');
			$button.html('Cancel');

			$('#content').prepend(self.$popup);
			self.$popup.slideDown(300);
			
			return evt.preventDefault();
		},
		
		cancel: function (self, evt) {
			self.state = 'default';
			
			self.$popup.slideUp(300);
			
			var $button = $(evt.target);
			$button.removeClass('cancel');
			$button.html(self.name);
			
			return evt.preventDefault();
		}
	},
	
	'action-connect': {
		default: function (self, evt) {
			self.state = 'cancel';
			
			if (!self.hasOwnProperty('$button')) {
				self.$button = $(evt.target);
				self.name = self.$button.html();
			}
			
			if (!self.hasOwnProperty('$popup')) {
				self.$popup = $('#accept_fee-div').clone();
			}
			
			var popup = new Popup('#content');
			
			self.$button.addClass('cancel');
			self.$button.html('Cancel');
			
			$('#content').prepend(self.$popup);
			self.$popup.slideDown(300);
			
			return evt.preventDefault();
		},
		
		cancel: function (self, evt) {
			self.state = 'default';
			
			self.$popup.slideUp(300);
			
			self.$button.removeClass('cancel');
			self.$button.html(self.name);
			
			return evt.preventDefault();
		}
	},
	
	'action-amazon-prompt': {
		default: function (self, evt) {
			self.state = 'cancel';
			
			if (!self.hasOwnProperty('$button')) {
				self.$button = $(evt.target);
				self.name = self.$button.html();
			}
			
			if (!self.hasOwnProperty('$popup')) {
				self.$popup = $('#configure-div').clone();
			}
			
			var popup = new Popup('#content');
			
			self.$button.addClass('cancel');
			self.$button.html('Cancel');
			
			$('#content').prepend(self.$popup);
			self.$popup.slideDown(300);
			
			return evt.preventDefault();
		},
		
		cancel: function (self, evt) {
			self.state = 'default';
			
			self.$popup.slideUp(300);
			
			self.$button.removeClass('cancel');
			self.$button.html(self.name);
			
			return evt.preventDefault();
		}
	},
	
	'action-amazon-verify': {
		default: function (self, evt) {
			self.state = 'cancel';
			
			if (!self.hasOwnProperty('$button')) {
				self.$button = $(evt.target);
				self.name = self.$button.html();
			}
			
			if (!self.hasOwnProperty('$popup')) {
				self.$popup = $('#verify-div').clone();
			}
			
			var popup = new Popup('#content');
			
			self.$button.addClass('cancel');
			self.$button.html('Cancel');
			
			$('#content').prepend(self.$popup);
			self.$popup.slideDown(300);
			
			return evt.preventDefault();
		},
		
		cancel: function (self, evt) {
			self.state = 'default';
			
			self.$popup.slideUp(300);
			
			self.$button.removeClass('cancel');
			self.$button.html(self.name);
			
			return evt.preventDefault();
		}
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
	}
};
