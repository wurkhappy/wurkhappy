/* ========================================================
 * Written by Brendan Berg
 * Copyright WurkHappy, 2011
 * ========================================================
 */



function addressIsValid(addr) {
	return addr.match(/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/);
}

$(document).ready(function () {
	
	//Faq page navigation
	//store the the navs lis, sections of content
	var $allNavs = $('.faqnav li');
	var $allSections = $('.section');
	
	$allNavs.click( function(event) {
		
		//Adjust current class on FAQ Nav li
		$allNavs.removeClass('current');
		$(this).closest('li').addClass('current');
		
		//Hide all the sections
		$allSections.hide();
		
		//Store the current sections's id
		var $currentSection = $(this).children().attr('href');
		
		//Show current section
		$($currentSection).show();
		
		event.preventDefault();
		
	});
	
	
	
	//Login overlay
	$('.login').hide();

	$('#login').click( function() {
		$('#copyright').addClass('fixed');
		$('#navigation').addClass('line');
		$('.login').show();
		$('.fade').fadeOut('fast');
	});
	
	//Tab click on landing page
	$('.tab').click(function () {
		// Get current elt's class, find corresponding container class
		// and adjust visibility. Set current class to current.
		var $button = $(this);
		console.log($button);
		
		if (!$button.hasClass('current')) {
			var id = $button.attr('id').match(/(\w+)-button/);
			console.log(id);
			
			if (id && id[1]) {
				$('.tab.current').toggleClass('current');
				$button.toggleClass('current');
				$('#content .tab-content').hide();
				$('#' + id[1] + '-container').show();
			}
		}
		
		return false;
	});
	
	$('.submit-button').click(function (event) {
		var self = this;
		var $form = $(this).closest('form');
		var $email = $form.find('input[name=email]');
		var $token = $form.find('input[name=_xsrf]');
		
		//TODO: Hide the signup form
		$email.blur();
		$(self).hide();
		$email.hide();
		$form.find('#email-label').hide();
		
		
		if (addressIsValid($email.val())) {
			var $header = $form.find('#form-header');
			var previousText = $header.text();
			
			$header.text('Sending...');
			
			$.ajax({
				url: '/signup.json',
				type: 'POST',
				data: {
					'email': $email.val(),
					'_xsrf': $token.val()
				},
				dataType: 'json',
				success: function (data, status, xhr) {
					if (data['success']) {
						$email.val('');
						$(self).remove();
						$form.find('#form-header').text('Thank you!');
						$form.append('<p>We will contact you soon with more information.</p>');
					} else {
						alert(data['message']);
					}
				},
				error: function (xhr, status, error) {
					var data = $.parseJSON(xhr.responseText);
					$form.find('#form-header').text(previousText);
					$(self).show();
					$email.show();
					$form.find('#email-label').show();
					$email.select();
					$email.focus();
					alert(data['message']);
				}
			});
		} else {
			$(self).show();
			$email.show();
			$form.find('#email-label').show();
			$email.select();
			$email.focus();
			$('.validation').html('Please enter a valid email');
			$('input#email-field').addClass('border');
			
		}
		return false;
	});
});

