/*
                     _      _                             
__      ___   _ _ __| | __ | |__   __ _ _ __  _ __  _   _ 
\ \ /\ / / | | | '__| |/ / | '_ \ / _` | '_ \| '_ \| | | |
 \ V  V /| |_| | |  |   <  | | | | (_| | |_) | |_) | |_| |
  \_/\_/  \__,_|_|  |_|\_\ |_| |_|\__,_| .__/| .__/ \__, |
                                       |_|   |_|    |___/ 
*/

var data = {items:[
	{value: "01", name: "Brendan Berg"},
	{value: "02", name: "Marcus Ellison"},
	{value: "03", name: "Frank Saulter"},
	{value: "04", name: "Matt Tretin"},
	{value: "05", name: "James Callender"},
	{value: "06", name: "Scott Siegel"},
	{value: "07", name: "David Lynch"},
	{value: "08", name: "Milton Glasser"},
	{value: "09", name: "Mike Bloomberg"},
	{value: "10", name: "Spencer Finch"},
	{value: "11", name: "George Bush"},
	{value: "12", name: "Nick D'Angelo"}
]};

function getCookie(name) {
	var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
	return c ? c[1] : undefined;
}

jQuery.postJSON = function(url, data, callback) {
	data._xsrf = getCookie("_xsrf");
	$.ajax({
		url: url,
		data: $.param(data),
		dataType: "text",
		type: "POST",
		success: callback
	});
}

$(document).ready(function() {
	$.getJSON("/user/me/contacts.json", null, function (data, status, xhr) {
		$("input#client-suggest").autoSuggest(data.contacts, {selectedItemProp: "name", searchObjProps: "name,email"});
	});
	
	$("#confirm-edit-button").click(function() {
		var data = {};
		
		var textareas = $('form textarea');
		for (var i = 0, len = textareas.length; i < len; i++) {
			data[textareas[i].name] = textareas[i].value;
		}
		
		$.postJSON($("form").attr('action') + '.json', data, function(data, status, xhr) {
			alert('success');
		});
		return false;
	});
});