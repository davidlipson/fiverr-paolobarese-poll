$(document).ready(function(a){
	var urlParams = new URLSearchParams(window.location.search)
	var pid = urlParams.get("pid");

	$.get("/api/poll?pid=" + pid)
		.done(function(data){

			// setup canvas
			var canvas = $("canvas");
			var ctx = canvas[0].getContext("2d");
			var radius = canvas[0].height/2 - 15;
			var smallRadius = radius - 50;

			// load poll information
			var question = "";
			var options = "";
			var status = "";

			// actual point of vote
			var point = {};

			// point on mouse down or notification
			var lastPoint = {};

			// start/mousedown coord
			var start = {};

			// offset from start
			var offset = {};

			// if mouse clicked/moving
			var clicked = false;

			init(data.data);

			function init(data){

				question = data.question;
				options = data.options;
				status = data.status;

				$(".query-text").html(data.question);
				$("#status-bar").html(data.status);
				$("#n-voters").html(data.viewers);
				updateWinners(data.winners);

				// actual point of vote
				point = {x: data.x, y: data.y};

				// point on mouse down or notification
				lastPoint = {x: data.x, y: data.y};

				// start/mousedown coord
				start = {x: canvas[0].width/2, y: canvas[0].height/2};

				// offset from start
				offset = {x: canvas[0].width/2, y: canvas[0].height/2};

				// if mouse clicked/moving
				clicked = false;

				redraw();

			}

			function updateWinners(winners){
				$(".winners-list").empty();
				winners.forEach(function(w){
					var li = $("<li></li>");
					li.html(w);
					$(".winners-list").append(li);
				});
			}


			// setup pusher connections
			const pusher = new Pusher("918ee8d39b9cdd619aeb", {
				cluster: "us2",
				encrypted: true
			});

			const channel = pusher.subscribe(pid);
			channel.bind("notify-move", handleMove);
			channel.bind("notify-status", handleStatus);
			channel.bind("notify-viewers", handleViewers);
			channel.bind("notify-reset", handleReset);

			function handleViewers(data){
				$("#n-voters").html(data.total);
			}

			function handleReset(data){
				init(data);
			}

			function handleMove(data){
				point.x = data.x;
				point.y = data.y;
				lastPoint.x = point.x;
				lastPoint.y = point.y;

				redraw();
			}

			function handleStatus(data){
				status = data.status;
				$("#status-bar").html(data.status)
				if(data.status == "COMPLETED"){
					leave();
					updateWinners(data.winners);
				} 
			}

			$("#start-button").click(function(a){
				var pass = prompt("Please enter the password to start:");

				if(pass != null){
					$.get("/api/start?pid=" + pid + "&password=" + pass)
						.fail(function(){
							alert("Invalid password.");
						})
				}
			})

			$("#stop-button").click(function(a){
				var pass = prompt("Please enter the password to start:");
				if(pass != null){
					$.get("/api/stop?pid=" + pid + "&password=" + pass)
						.fail(function(){
							alert("Invalid password.");
						})
				}
			})

			$("#reset-button").click(function(a){
				var pass = prompt("Please enter the password to start:");
				if(pass != null){
					$.get("/api/reset?pid=" + pid + "&password=" + pass)
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

				// entering
				$.get("/api/enter?pid=" + pid);

			});

			// same as above, but continues a path (as opposed to starting a new on mouse down)
			$('canvas').mousemove(function(e){
				if(clicked && status == "STARTED"){
					offset.x = (e.pageX - this.offsetLeft) - start.x;
					offset.y = (e.pageY - this.offsetTop) - start.y;
					start.x = (e.pageX - this.offsetLeft);
					start.y = (e.pageY - this.offsetTop);

					point.x = point.x + offset.x;
					point.y = point.y + offset.y;

					redraw();

					if(Math.sqrt((point.x - lastPoint.x)**2 + (point.y - lastPoint.y)**2) > 20){
						notifyMove(point.x - lastPoint.x,  point.y - lastPoint.y);
						lastPoint.x = point.x;
						lastPoint.y = point.y;
					}
				}
			});

			// end paths
			$('canvas').mouseup(function(e){ leave(); });
			$('canvas').mouseleave(function(e){ leave(); });

			function leave(){
				if(clicked){
					clicked = false;

					// leaving
					$.get("/api/leave?pid=" + pid);	
				}
			}

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
				    				(current_dist > smallRadius && status == "COMPLETED" ? "red" : "yellow") : "white";
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

			function notifyMove(offsetX, offsetY){
				$.post("/api/notifyMove", {offsetX: offsetX, offsetY: offsetY, pid: pid, x: point.x, y: point.y})
					.fail(function(){
						leave();
					});
			}

		})
		.fail(function(){
			alert("There was an error loading this poll.");
			window.location = "/";
		});

	
	
});