/* ========================================================
 * Written by Brendan Berg
 * Copyright WurkHappy, 2011
 * ========================================================
 */



function addressIsValid(addr) {
	return addr.match(/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/);
}

$(document).ready(function () {
	$('#signup_form').submit(function (event) {
		var emailAddress = $('input[name=email]').val();
		var xsrfToken = $('input[name=_xsrf]').val();
		
		$('#form_email').blur();
		$('#signup_form').hide();
		
		if (addressIsValid(emailAddress)) {
			$.ajax({
				url: '/signup.json',
				type: 'POST',
				data: {
					"email": emailAddress,
					"_xsrf": xsrfToken
				},
				dataType: 'json',
				success: function (data, status, xhr) {
					if (data['success']) {
						$('#form_email').val('');
						$('#signup_form').remove();
						$('#header_text').text('Thank you!');
						$('#tagline_text').text('We will contact you soon with more information.');
					} else {
						console.log('AJAX error: ' + data['message']);
						alert(data['message']);
					}
				},
				error: function (xhr, status, error) {
					var data = $.parseJSON(xhr.responseText);
					console.log('AJAX error: ' + data['message']);
					alert(data['message']);
					$('#signup_form').show();
					$('#form_email').select();
					$('#form_email').focus();
				}
			});
		} else {
			console.log('JavaScript email validation error');
			alert('I\'m sorry, that didn\'t look like a proper email address. Could you please enter a valid email address?');
			$('#signup_form').show();
			$('#form_email').select();
			$('#form_email').focus();
		}
		
		return false;
	});
});

