var buttonActions = {
	
	'action-send-invitation': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			
			$.ajax({
				url: '/user/' + slug['userID'] + '.json',
				data: {'action': 'send_invitation', '_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Sent invitation').open();
					self.$elt.attr('id', 'action-send-password-reset').html('Send Password Reset');
					self.actions = buttonActions[self.$elt.attr('id')];
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-send-password-reset': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			
			$.ajax({
				url: '/user/' + slug['userID'] + '.json',
				data: {'action': 'send_password_reset', '_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Sent password reset instructions').open();
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-lock-account': {
		default: function (self, evt) {
			// var popup = new Popup('#content');
			
			$.ajax({
				url: '/user/' + slug['userID'] + '.json',
				data: {'action': 'lock_account', '_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					self.$elt.attr('id', 'action-unlock-account').html('Unlock Account');
					self.actions = buttonActions[self.$elt.attr('id')];
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-unlock-account': {
		default: function (self, evt) {
			// var popup = new Popup('#content');
			
			$.ajax({
				url: '/user/' + slug['userID'] + '.json',
				data: {'action': 'unlock_account', '_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
				//	popup.setLabel('Account unlocked').open();
					self.$elt.attr('id', 'action-lock-account').html('Lock Account');
					self.actions = buttonActions[self.$elt.attr('id')];
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-reset-amazon-payments': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			
			$.ajax({
				url: '/user/' + slug['userID'] + '.json',
				data: {'action': 'reset_amazon', '_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Reset Amazon Payments account info').open();
					self.$elt.slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	}
};