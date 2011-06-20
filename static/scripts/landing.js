/* ========================================================
 * Written by Brendan Berg
 * Copyright WurkHappy, 2011
 * ========================================================
 */

$(document).ready(function () {
	$('#signup_form').onSubmit(function (self) {
		$('#form_email').val('');
		// $.ajax({
		// 	url: '/signup',
		// 	success: function (data, status, xhr) {
		// 		$('#signup_form').remove();
		// 		$('').append('<h1>Thank you!</h1>');
		// 	},
		// 	error: function (xhr, status, error) {
		// 		console.log('AJAX error: ' + error);
		// 	}
		// });
		
		return false;
	});
});

