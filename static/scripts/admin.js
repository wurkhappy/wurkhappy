var buttonActions = {
	
	'action-send-invitation': {
		default: function (self, evt) {
			// var popup = new Popup('#content');
			
			$.ajax({
				url: '/user/' + slug['userID'] + '.json',
				data: {'action': 'send_invitation', '_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Sent invitation').open();
					$('#action-save').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	},
	
	'action-send-password-reset': {
		default: function (self, evt) {
			// var popup = new Popup('#content');
			
			$.ajax({
				url: '/user/' + slug['userID'] + '.json',
				data: {'action': 'send_password_reset', '_xsrf': slug['_xsrf']},
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					popup.setLabel('Sent password reset instructions').open();
					$('#action-save').slideUp(300);
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
					//$();
					popup.setLabel('Account locked').open();
					$('#action-save').slideUp(300);
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
					popup.setLabel('Account unlocked').open();
					$('#action-save').slideUp(300);
				},
				error: self.errorHandler
			});
			
			return evt.preventDefault();
		}
	}
}