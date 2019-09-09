$(document).ready(function(a){
	var urlParams = new URLSearchParams(window.location.search)
	var pid = urlParams.get("pid");

	$.get("/api/poll?pid=" + pid)
		.done(function(data){

			// load poll information
			var question = data.data.question;
			var options = data.data.options;

			$(".query-text").html(question);
			$("#status-bar").html(data.data.status)

			// setup canvas
			var canvas = $("canvas");
			var ctx = canvas[0].getContext("2d");
			var radius = canvas[0].height/2 - 15;
			var smallRadius = radius - 50;

			// actual point of vote
			var point = {x: data.data.x, y: data.data.y};

			// start/mousedown coord
			var start = {x: canvas[0].width/2, y: canvas[0].height/2};

			// offset from start
			var offset = {x: canvas[0].width/2, y: canvas[0].height/2};

			// if mouse clicked/moving
			var clicked = false;

			// setup pusher connections
			const pusher = new Pusher("918ee8d39b9cdd619aeb", {
				cluster: "us2",
				encrypted: true
			});

			const channel = pusher.subscribe(pid);
			channel.bind("notify-move", handleMove);
			channel.bind("notify-status", handleStatus);


			function handleMove(data){
				point.x = data.x;
				point.y = data.y;
				redraw();
			}

			function handleStatus(data){
				$("#status-bar").html(data.status)
			}

			redraw();

			$("#start-button").click(function(a){
				var pass = prompt("Please enter the password to start:");

				if(pass != null){
					$.get("/api/start?pid=" + pid + "&password=" + pass)
						.done(function(data){
							console.log(data);
						})
						.fail(function(){
							alert("Invalid password.");
						})
				}
			})

			$("#stop-button").click(function(a){
				var pass = prompt("Please enter the password to start:");
				if(pass != null){
					$.get("/api/stop?pid=" + pid + "&password=" + pass)
						.done(function(data){
							console.log(data);
						})
						.fail(function(){
							alert("Invalid password.");
						})
				}
			})

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
				var current_dist = Math.sqrt((point.y - canvas[0].height/2)**2 + (point.x - canvas[0].width/2)**2)
				if(current_angle < 0) current_angle = Math.PI * 2 + current_angle;
				
			    for(var i = 0; i < options.length; i = i + 1) {
			    	var angle = Math.PI * 2 / options.length;
			    	var beginAngle = angle * i;
				    var endAngle = beginAngle + angle;
				    var medianAngle = (endAngle + beginAngle) / 2;
				    ctx.beginPath();
				    ctx.fillStyle = (current_angle >= beginAngle && current_angle < endAngle) ? 
				    				(current_dist > smallRadius ? "red" : "yellow") : "white";
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
					ctx.fillText(options[i], radius * Math.cos(medianAngle) + canvas[0].width/2, radius * Math.sin(medianAngle) + canvas[0].height/2);
				}

				ctx.beginPath();
				ctx.arc(canvas[0].width/2, canvas[0].height/2, smallRadius, 0, 2 * Math.PI);
				ctx.stroke();

				// point
				ctx.fillRect(point.x - 5, point.y - 5, 10, 10);
			}
			function notifyMove(){
				$.post("/api/notifyMove", {offsetX: offset.x, offsetY: offset.y, pid: pid, x: point.x, y: point.y})
					.done(function(data){
						point.x = data.new_point.x;
						point.y = data.new_point.y;
						console.log(data);
					})
					.fail(function(){
						alert("Cannot vote at this time.");
						clicked = false;
					});
			}

		})
		.fail(function(){
			alert("There was an error loading this poll.");
			window.location = "/";
		});

	
	
});