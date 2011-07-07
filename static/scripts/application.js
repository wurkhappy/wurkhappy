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
	{value: "07", name: "Owen Wilson"},
	{value: "08", name: "Milton Glasser"},
	{value: "09", name: "Mike Bloomberg"},
	{value: "10", name: "Spencer Finch"},
	{value: "11", name: "George Bush"},
	{value: "12", name: "Nick D'Angelo"}
]};

$(document).ready(function() {
	$("input#client-suggest").autoSuggest(data.items, {selectedItemProp: "name", searchObjProps: "name"});
});