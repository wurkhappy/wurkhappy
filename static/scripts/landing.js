/* ========================================================
 * Written by Brendan Berg
 * Copyright WurkHappy, 2011
 * ========================================================
 */

function getCookie(name) {
	var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
	return c ? c[1] : undefined;
}

function addressIsValid(addr) {
	return addr.match(/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/);
}



$(document).ready(function() {
	
	var elements = document.getElementsByTagName("INPUT");
  for (var i = 0; i < elements.length; i++) {
      elements[i].oninvalid = function(evt) {
          evt.target.setCustomValidity("");
          if (!evt.target.validity.valid) {
              evt.target.setCustomValidity("This field cannot be left blank");
          }
      };
      elements[i].oninput = function(evt) {
          evt.target.setCustomValidity("");
      };
  }
		
	$('.faqnav li:not(.title)').click( function(event) {
		
		//Faq page navigation
		//store the the navs lis, sections of content
		var $allNavs = $('.faqnav li:not(.title)');
		var $allSections = $('.section');
		
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
	$('#log_out').hide();
	
	var t1, t2;
	
	$('#login').on('click', function(evt) {		
		
		// delay the focus function on the email input so that the function isn't called until
		// after the login appears.
		// wrap it in setTimeout because delay is limited
		// set an identifier to SetTimeout so that it can be cleared later on.
		
		t1 = setTimeout(function() {
			$('.login').fadeIn('fast');
		}, 200);
		
		t2 = setTimeout(function() {
			$('#target').focus();
		}, 300);
		
		
		
		// hide stuff, show stuff, add class, fade stuff
		$('#log_in').hide();
		$('#log_out').show();
		$('#copyright').addClass('fixed');
		$('#navigation').addClass('line');
		$('.fade').fadeOut('fast');
		
		//hide error messages from other form
		$('#server_error').html('');
		$('.validation').html('');
		$('input#email-field').removeClass('border');
		
		evt.preventDefault();
	});
	
	//Do the same thing as above but opposite
	$('#cancel').click( function(e) {
		$('#log_out').hide();
		$('#log_in').show();
		$('#copyright').removeClass('fixed');
		$('#navigation').removeClass('line');
		$('.login').fadeOut('fast');
		$('.fade').fadeIn('slow');
		
		clearTimeout(t1);
		clearTimeout(t2);
		
		//hide error messages from other form
		$('#server_error').html('');
		$('.validation').html('');
		$('input#email-field').removeClass('border');
		
		e.preventDefault();

	});
	
	//Tab click on landing page
	$('.tab').click(function () {
		// Get current elt's class, find corresponding container class
		// and adjust visibility. Set current class to current.
		var $button = $(this);
		
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
	
	$('#login_form').on('submit', function (evt) {
		evt.preventDefault();
		var self = this;
		var $form = $(this).closest('form');
		var $email = $form.find('input[name=email]');
		var $passwd = $form.find('input[name=password]');
		
		if (addressIsValid($email.val())) {
			var $header = $form.find('#form-header');
			var previousText = $header.text();
			
			$header.text('Sending...');			
			
			$.ajax({
				url: 'https://beta.wurkhappy.com/login.json',
				type: 'POST',
				data: {
					'email': $email.val(),
					'password': $passwd.val()
				},
				xhrFields: {withCredentials: true},
				crossDomain: true,
				dataType: 'json',
				success: function (data, status, xhr) {
					if (data['user']) {
						// TODO: Redirect to https://beta.wurkhappy.com/
						// (Actually https://sandbox.wurkhappy.com/ until the patch I uploaded today goes live.)
						window.location.href = 'https://beta.wurkhappy.com/';
			
						$passwd.val('');
						$email.val('');
						$('#server_error').html('');
						
						
					} else {
						alert('Something went wrong on the server. Please try again later.');
					}
				},
				error: function (xhr, status, error) {
					
					var data = $.parseJSON(xhr.responseText);
					$form.find('#form-header').text(previousText);
					$passwd.val('');
					$email.val('');
					$passwd.select();
					$passwd.focus();
					$('#login_form').addClass('invalid');
					$('#server_error').html('Please enter a valid email or password');
					$('input#email-field').addClass('border');
					$('.validation').html('');
				}
			});
		} else if ($passwd.val() !== '') {
			$(self).show();
			$email.show();
			$form.find('#email-label').show();
			$email.select();
			$email.focus();
			$('.validation').html('Please enter a password');
			$('input#email-field').addClass('border');
		} else {
			$(self).show();
			$email.show();
			$form.find('#email-label').show();
			$email.select();
			$email.focus();
			$('.validation').html('Please enter a valid email');
			$('input#email-field').addClass('border');
			
		}
	});
	
	$('#create_form').on('submit', function (evt) {
		var $form = $(this).closest('form');
		var $email = $form.find('input[name=email]');
		
		if (!addressIsValid($email.val())) {
			$email.select();
			$email.focus();
			$('.validation').html('Please enter a valid email');
			$('input#email-field').addClass('border');
			evt.preventDefault();
		}
	});
	
	// clear error messages when login/create forms are clicked
	$('#login_form').click( function(evt) {
		$('#server_error').html('');
		$('.validation').html('');
		$('#login_form').removeClass('invalid');
	});
	
	$('#create_form').click( function(evt) {
		$('#server_error').html('');
		$('.validation').html('');
		$('input#email-field').removeClass('border');
	});
	
});

