var Accordion = {
	init: function() {
		$('#phases').accordion({
			header: 'h2'
		});
		$('#phases .add-phase').click(function(e) {
			e.preventDefault();
			var nextPhase = $(this).parents('li').next('li');
			$(this).remove();  
			Accordion.addPane(nextPhase);
		});
	},
	addPane: function(nextPhase) {
		nextPhase.show();
		nextPhase.find('h2').click();
	}
};

Accordion.init();