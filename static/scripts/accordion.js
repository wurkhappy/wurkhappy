var Accordion = {
	init: function() {
		$('#phases').accordion({
			header: 'h3'
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