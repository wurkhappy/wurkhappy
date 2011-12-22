var Accordion = {
	init: function() {
		$('#phases').accordion({
			header: 'h2'
		});

		$('#phases .add-phase').click(function(e) {
			e.preventDefault();		
			var phasesToAdd = $(this).parents('li').siblings().filter(':hidden');
			var nextPhase = phasesToAdd.first();
			
			if (phasesToAdd.length === 1) {
				$('#phases .add-phase').remove();
			}
			
			Accordion.addPane(nextPhase);
		});
	},
	addPane: function(nextPhase) {
		nextPhase.show();
		nextPhase.find('h2').click();
	}
};

Accordion.init();