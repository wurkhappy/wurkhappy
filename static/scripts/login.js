var wurkHappy = {
	User: function (properties) {
		this.id = properties['id'];
		this.fullName = properties['fullName'];
		this.email = properties['email'];
		this.profileURL = properties['profileURL'];
		this.telephone = properties['telephone'];
	}
}

var buttonActions = {
	
	'login': {
		default: function (self, evt) {
			var popup = new Popup('#content');
			var bodyString = self.serialize('login_form');
			
			$.ajax({
				url: '/login.json',
				data: bodyString,
				dataType: 'json',
				type: 'POST',
				success: function (data, status, xhr) {
					self.state = 'disabled';
					$(evt.target).addClass('disabled');
					
					$('#password-form input').val('');
					
					var redirectURL = xhr.getResponseHeader('Location') || '/';
					
					window.location.href = redirectURL;
				},
				error: function (jqXHR, textStatus, errorThrown) {
					var error = jQuery.parseJSON(jqXHR.responseText);
					popup.setLabel(error ? error.display : 'Your password was incorrect.').open();
					$('#login_form input[type=password]').val('');
				}
			});
			
			return evt.preventDefault();
		}
	}
};
