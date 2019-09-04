$(document).ready(function(a){
	var options = $('<div class="options-body"><div class="options"></div><img class="svg-button" id="add-option" src="./static/svg/plus.svg"></div>');
	$(".poll-body").append(options);

	// add option
	$("#add-option").click(function(){
		var o = $('<div class="option-body"><div class="remove-option"><img class="svg-button" src="./static/svg/x.svg"></div><div class="option-text"><input type="text" placeholder="Create new option..."></div></div>')
		$(".options", options).append(o);
		
		// remove option row
		$(".remove-option").click(function(){
			$(this).parent().remove();
			var r = validateInput();
		});

		// update disabled button on text input
		$("input").keyup(function(){
			var r = validateInput();
		});
	});

	// create button click
	$("button").click(function(){
		var r = validateInput();
		console.log(r);
		if(r){
			if (confirm("Finalize this poll?") == true){

				// insecure password for owner of poll
				var pass = prompt("Please enter a password - only you as the poll owner should use this password when entering the poll.");
				r["password"] = pass
				
				$.post("/api/generate", r)
					.done(function(data){
						var pid = data.pid;
						window.location = "/poll?pid=" + pid;

					})
					.fail(function(){
						alert("There was an error");
					});
			}
		}
		else{
			alert("Invalid input - require a question and at least 2 options.");
		}
	})


	// validate question and options input for submitting
	function validateInput(){
		// verify question
		var q = $(".question-body input").val();

		// verify options
		var options = []
		$(".option-body input").toArray().forEach(function(i){
			if(i.value != ""){
				options.push(i.value);
			}
		})

		// question and at least two options
		if (q != "" && options.length >= 2){
			// enable create button
			$('button').prop('disabled', false);
			

			// return question and options
			var r = {
				question: q,
				options: options
			};

			return r;
		}
		else{
			// disable create button
			$('button').prop('disabled', true);
			return false;
		}
	}


});