$(document).ready(function(){
    var visible = 1;
    $("#addrow").click(function(){
    	var next = visible + 1;
    	$("#row-" + next).toggle();
	visible = visible + 1;
	if (visible == 10){
		$(this).toggle();
	};
    });
});
