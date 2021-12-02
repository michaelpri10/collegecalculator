$(document).ready(function() {
    $("#state").select2();
    $("#distance").select2();
    $("#campus-location").select2();
    $("#enrollment").select2();
    $("#study-fields").select2();
    $("#tuition").on
    var tuition = document.querySelector("#tuition");
    var tuition_output = document.querySelector("#tuition-output");
    tuition.addEventListener("input", function() {
        tuition_output.innerHTML = tuition.value;
    });

    var sat_math = document.querySelector("#sat-math");
    var sat_math_output = document.querySelector("#sat-math-output");
    var sat_reading = document.querySelector("#sat-reading");
    var sat_reading_output = document.querySelector("#sat-reading-output");
    var act = document.querySelector("#act");
    var act_output = document.querySelector("#act-output");

    sat_math.addEventListener("input", function() {
        sat_math_output.innerHTML = sat_math.value;
    });
    sat_reading.addEventListener("input", function() {
        sat_reading_output.innerHTML = sat_reading.value;
    });
    act.addEventListener("input", function() {
        act_output.innerHTML = act.value;
    });

    var location_step = document.querySelector("#location-step");
    var majors_step = document.querySelector("#majors-step");
    var finance_step = document.querySelector("#finance-step");
    var other_step = document.querySelector("#other-step");

    var location_button = document.querySelector("#location-button");
    var majors_button = document.querySelector("#majors-button");
    var finance_button = document.querySelector("#finance-button");
    var other_button = document.querySelector("#other-button");

    location_button.addEventListener("click", function() {
        location_step.style.display = "none";
        majors_step.style.display = "flex";
    });
    majors_button.addEventListener("click", function() {
        majors_step.style.display = "none";
        finance_step.style.display = "flex";
    });
    finance_button.addEventListener("click", function() {
        finance_step.style.display = "none";
        other_step.style.display = "flex";
    });

    var majors_back = document.querySelector("#majors-back");
    var finance_back = document.querySelector("#finance-back");
    var other_back = document.querySelector("#other-back");

    majors_back.addEventListener("click", function() {
        majors_step.style.display = "none";
        location_step.style.display = "flex";
    });
    finance_back.addEventListener("click", function() {
        finance_step.style.display = "none";
        majors_step.style.display = "flex";
    });
    other_back.addEventListener("click", function() {
        other_step.style.display = "none";
        finance_step.style.display = "flex";
    });
});
