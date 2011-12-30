
var buttonActions = {
	
	'action-save': {
		default: function (self, evt) {
			// validate..
			// var commentLength = ...
			
			var capture = self.serialize('agreement-form');
			var formAction = $('#agreement-form').attr('action');
			
			$.ajax({
				url: formAction + '/save.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					alert('Your changes have been saved');
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
			
			$.ajax({
				url: formAction + '/send.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					alert('Successfully sent estimate');
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
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/send.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					alert('Successfully sent estimate');
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
			if (commentLength > 0) {
				alert('By accepting the estimate, no additional comments are allowed so your notes will not be sent-- save them while you can!');
				return evt.preventDefault();
			}
			
			var capture = self.serialize('comments-form');
			
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/accept.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					alert('Successfully accepted estimate');
					$('.action-button li').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-decline': {
		default: function (self, evt) {
			var commentLength = formValidator.checkCommentLength($('textarea'));
			if (commentLength < 10) {
				alert('Please add a few comments (reasons for declining, questions, etc.) regarding the estimate.');
				return evt.preventDefault();
			}
			
			var capture = self.serialize('comments-form');
			console.log(capture);
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/decline.json',
				data: capture,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					alert('Your request for changes has been sent');
					$('.action-button li').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-markcomplete': {
		default: function (self, evt) {
			var bodyString = self.serialize();
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/mark_complete.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					alert('The work outlined in the current phase has been marked complete');
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
			
			var bodyString = self.serialize('comments-form');
			console.log(bodyString);
			$.ajax({
				url: '/agreement/' + slug['agreementID'] + '/dispute.json',
				data: bodyString,
				dataType: "json",
				type: 'POST',
				success: function (data, status, xhr) {
					alert('Successfully disputed the work completed');
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
			
			var bodyString = self.serialize('form');
			$.ajax({
				url: '/agreement/request.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					alert('Successfully sent your request');
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
			
			if (!self.$popup) {
				self.$popup = $('<div class="clear prompt-box" id="password-div" style="display:none;">\
		<form id="password-form" class="invisible">\
			<div class="column-three-fourth">\
				<h3>Submitting payment of \
					<span id="verify-amount">$0.00</span> from account ending in \
					<span id="verify-account">----</span>\
				</h3>\
				<fieldset class="no-border">\
					<label for="password">Enter your password to approve and send payment.</label><br />\
					<input type="password" name="password" />\
				</fieldset>\
			</div>\
			<div class="column-one-fourth">\
				<fieldset class="submit-buttons no-border">\
					<input type="submit" id="prompt-submit-button" value="Submit Payment">\
				</fieldset>\
			</div>\
		</form></div>');
				self.$popup.find('#verify-amount').html(slug['currentPhase']['amount']);
				self.$popup.find('#verify-account').html(slug['account']);
				self.$popup.children('#password-form').submit(function(evt) {
					var capture = self.serialize('password-form', {'agreementID': slug['agreementID']});
					console.log(capture);
					$.ajax({
						url: '/payment/new.json',
						data: capture,
						dataType: 'json',
						type: 'POST',
						success: function(data, status, xhr) {
							alert('Successfully verified the work completed');
							$('.action-button li').slideUp(300);
							$('#password-div').slideUp(300);
						},
						error: self.errorHandler
					});
					
					return evt.preventDefault();
				});
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
	}
};
