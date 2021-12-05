$(document).ready(function() { 
	var interests_step = document.querySelector("#interests-step"); 
	var values_step = document.querySelector("#values-step");
	var talents_step = document.querySelector("#talents-step"); 
	var qualities_step = document.querySelector("#qualities-step");
	
	var interests_button = document.querySelector("#interests-button");
    var values_button = document.querySelector("#values-button"); 
	var talents_button = document.querySelector("#talents-button");
    var qualities_button = document.querySelector("#qualities-button");

	interests_button.addEventListener("click", function() {
        interests_step.style.display = "none";
        values_step.style.display = "flex";
    });  
	
	values_button.addEventListener("click", function() {
        values_step.style.display = "none";
        talents_step.style.display = "flex";
    }); 

	talents_button.addEventListener("click", function() {
        talents_step.style.display = "none";
        qualities_step.style.display = "flex";
    }); 

    var values_back = document.querySelector("#values-back");
    var talents_back = document.querySelector("#talents-back");
    var qualities_back = document.querySelector("#qualities-back");
    
	values_back.addEventListener("click", function() {
        values_step.style.display = "none";
        interests_step.style.display = "flex";
    });

    talents_back.addEventListener("click", function() {
        talents_step.style.display = "none";
        values_step.style.display = "flex";
    });

    qualities_back.addEventListener("click", function() {
        qualities_step.style.display = "none";
        values_step.style.display = "flex";	
	}


});
