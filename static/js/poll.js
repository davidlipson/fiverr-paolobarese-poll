$(document).ready(function(a){
	$.get("/api/poll")
		.done(function(data){

			// load poll information
			var question = data.data.question;
			var options = data.data.options;

			$(".query-text").html(question);

			// setup canvas
			var canvas = $("canvas");
			var ctx = canvas[0].getContext("2d");
			var radius = canvas[0].height/2 - 15;

			// actual point of vote
			var point = {x: canvas[0].width/2, y: canvas[0].height/2};

			// start/mousedown coord
			var start = {x: canvas[0].width/2, y: canvas[0].height/2};

			// offset from start
			var offset = {x: canvas[0].width/2, y: canvas[0].height/2};

			// if mouse clicked/moving
			var clicked = false;

			redraw();

			/////////////////// Mouse movement functionality /////////////////

			// mouse/drawing functionality
			$('canvas').mousedown(function(e){
				clicked = true;
				start.x = (e.pageX - this.offsetLeft);
				start.y = (e.pageY - this.offsetTop);
			});

			// same as above, but continues a path (as opposed to starting a new on mouse down)
			$('canvas').mousemove(function(e){
				if(clicked){
					offset.x = (e.pageX - this.offsetLeft) - start.x;
					offset.y = (e.pageY - this.offsetTop) - start.y;
					start.x = (e.pageX - this.offsetLeft);
					start.y = (e.pageY - this.offsetTop);
					notifyMove();
					redraw();
				}
			});

			// end paths
			$('canvas').mouseup(function(e){ clicked = false; });
			$('canvas').mouseleave(function(e){ clicked = false; });

			function redraw(){
				// blank screen
				ctx.clearRect(0,0,canvas[0].width,canvas[0].height);

				// border
				ctx.beginPath();
				ctx.arc(canvas[0].width/2, canvas[0].height/2, radius, 0, 2 * Math.PI);
				ctx.stroke();

				// draw options
				var offset = 10;
				var beginAngle = 0;
				var endAngle = 0;
				var offsetX, offsetY, medianAngle;

				// calculate current angle and quadrant
				var current_angle = Math.atan2(point.y-canvas[0].height/2, point.x-canvas[0].width/2);
				if(current_angle < 0) current_angle = Math.PI * 2 + current_angle;
				
			    for(var i = 0; i < options.length; i = i + 1) {
			    	var angle = Math.PI * 2 / options.length;
			    	var beginAngle = angle * i;
				    var endAngle = beginAngle + angle;
				    var medianAngle = (endAngle + beginAngle) / 2;
				    console.log(beginAngle, current_angle, medianAngle, options[i]);
				    ctx.beginPath();
				    ctx.fillStyle = (current_angle >= beginAngle && current_angle < endAngle) ? "yellow" : "white";
				    ctx.moveTo(canvas[0].width/2, canvas[0].height/2);
				    ctx.arc(canvas[0].width/2, canvas[0].height/2, radius, beginAngle, endAngle);
				    ctx.lineTo(canvas[0].width/2, canvas[0].height/2);
				    ctx.stroke();
				    ctx.fill();
				}

				ctx.fillStyle = "black";
				ctx.font = "20px Georgia";
				for(var i = 0; i < options.length; i = i + 1) {
			    	var angle = Math.PI * 2 / options.length;
			    	var beginAngle = angle * i;
				    var endAngle = beginAngle + angle;
				    var medianAngle = (endAngle + beginAngle) / 2;
				    console.log(radius * Math.cos(beginAngle), radius * Math.sin(beginAngle));
					ctx.fillText(options[i], radius * Math.cos(medianAngle) + canvas[0].width/2, radius * Math.sin(medianAngle) + canvas[0].height/2);
				}

				// point
				ctx.fillRect(point.x - 5, point.y - 5, 10, 10);
			}
			function notifyMove(){
				$.post("/api/notifyMove", {x: offset.x, y: offset.y})
					.done(function(data){
						point.x += data.offset.x;
						point.y += data.offset.y;
					})
					.fail(function(){
						console.log("Notify Move Failed.")
					});
			}

		})
		.fail(function(){
			alert("There was an error loading this poll.")
		});

	
	
});