$(document).ready(function() { 

    var interests_step = document.querySelector("#interests-step"); 
	var strengths_step = document.querySelector("#strengths-step");

    var interests_button = document.querySelector("#interests-button");
    var strengths_button = document.querySelector("#strengths-button");

    interests_button.addEventListener("click", function() {
        interests_step.style.display = "none";
        strengths_step.style.display = "flex";
    }); 

	checkboxes = document.getElementsByName('interests');
	  for(var i=0, n=checkboxes.length;i<n;i++) {
		      checkboxes[i].checked = source.checked;
	  }


});
