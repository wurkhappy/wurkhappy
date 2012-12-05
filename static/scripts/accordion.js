var Accordion = {
	init: function() {
		$('#phases').find('h3').css('cursor', 'pointer').click(function(evt) {
			var $containers = $(evt.target).parent().siblings('li');
			$containers.removeClass('wh-current');
			$(evt.target).parent().addClass('wh-current');
			$(evt.target).parent().children('div').slideDown();
			$containers.filter(':not(.wh-current)').children('div').slideUp();
		});

		$('#add-phase-btn').click(function(e) {
			e.preventDefault();		
			var phasesToAdd = $(this).parent().siblings('ul').children('li').filter(':hidden');
			var nextPhase = phasesToAdd.first();
			
			if (phasesToAdd.length === 1) {
				$('#add-phase-btn').remove();
			}
			
			Accordion.addPane(nextPhase);
		});
	},
	addPane: function(nextPhase) {
		nextPhase.show();
		nextPhase.find('h3').click();
	}
};

Accordion.init();