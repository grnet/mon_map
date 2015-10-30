$(document).ready(function () {
	var svgDiv = $('#svg');
	var layers = [];
	var popup = $('#popup');

	popup.on('click', function () {
		popup.removeClass('open');
	});
	// loading bar
	NProgress.start();

	var mapUrl = $.getJSON(svgDiv.data('url'), function (data) {
		$('body').append(data.svg.style);
		var main = d3.select('#svg');
		var svg = main.append('svg')
				.attr('xmlns', 'http://www.w3.org/2000/svg')
				.attr('viewbox', data.svg.attrs.viewbox)
				.attr('width', '100%')
				.attr('preserveAspectRatio','xMinYMin meet')
				.attr('class', data.svg.css_class)
				.attr('height', data.svg.attrs.height);

		var tip = d3.tip()
			.direction('s')
			.attr('class', 'd3-tip')
			.html(function(d) { return  d; });
		svg.call(tip);
		var gOuter = svg.append('g');
		var labels = data.labels;
		for (var i=0; i < labels.length; i++) {
			var g = gOuter.append('text')
				.attr('transform', labels[i].transform)
				.attr('x', labels[i].x)
				.attr('y', labels[i].y)
				.text(labels[i].title)
		}
		var links = data.links;
		for (var i=0; i < data.links.length; i++) {
			if (layers.indexOf(links[i].layer) === -1 ) {
				layers.push(links[i].layer);
			}
			var g = gOuter.append('g')
				.attr('data-title', 'link')
				.attr('data-url', links[i].url)
				.attr('data-load-url', links[i].load_url)
				.attr('data-layer', links[i].layer)
				.attr('data-to', links[i].from)
				.attr('data-from', links[i].to)
				.attr('transform', links[i].transform)
				.attr('data-load', 'loading...')
				.on('mouseover', function () {
					tip.show(d3.select(this).attr('data-load'));
				})
				.on('mouseout', tip.hide);
			links[i].item = g;
			var shape = g.append(data.links[i].shape);
			for (a in data.links[i].shape_attrs) {
				shape.attr(a, data.links[i].shape_attrs[a]);
			}
			shape.attr('style', 'stroke: #555555');

		}
		var hosts = data.hosts;
		for (var host in hosts) {
			var g = gOuter.append('g')
				.attr('data-title', host)
				.attr('data-layer', hosts[host].layer)
				.attr('transform', hosts[host].transform)
				.on('mouseover', function () {
					tip.show(d3.select(this).attr('data-title'));
				})
				.on('mouseout', tip.hide);
			hosts[host].item = $(g);
			var shape = g.append(hosts[host].shape);
			for (a in hosts[host].shape_attrs) {
				shape.attr(a, hosts[host].shape_attrs[a]);
			}
		}
		var tags = data.svg_tags;
		for (var i=0; i < data.svg_tags.length; i++) {
			var g = gOuter.append('g')
				.attr('transform', data.svg_tags[i].transform)
			var shape = g.append(data.svg_tags[i].shape);
			for (a in data.svg_tags[i].shape_attrs) {
				shape.attr(a, data.svg_tags[i].shape_attrs[a]);
			}
		}

		function setColor(perc){
		   if (perc == 0){
				color = "#4000c3";
				return color;
			} else if (perc > 0 && perc <= 10) {
				color = "#3845c4";
				return color;
			}
			else if (perc > 10 && perc <= 25){
				color = "#009895";
				return color;
			}
			else if (perc > 25 && perc <= 40){
				color = "#00d92d";
				return color;
			}
			else if (perc > 40 && perc <= 70){
				color = "#8ad72d";
				return color;
			}
			else if (perc > 70 && perc <= 85){
				color = "#c66517";
				return color;
			}
			else if (perc > 85 && perc <= 100){
				color ="#c80003";
				return color;
			}
		}


		function get_graphs(url, from, to) {
			$.getJSON(url, function(data) {
				images = '<h4>From ' + from + ' to ' + to + '</h4>' + '<img src="' + data.Total + '">';
				$.each(data, function (key, value) {
					if (!(key === 'Total')) {
						images += '<h5>' + key + '</h5><a href="'+ value.link_to_mon + '" target="_blank"><button class="btn">View in mon</button></a><img src="' + value.png + '">';
					}
				})
				popup.find('.text').html(images);
			})
		}

		function show_details() {
			var start = timespan.find('#start').val();
			var end = timespan.find('#end').val();
			var from = $(this).parent().data('from');
			var to = $(this).parent().data('to');
			popup.addClass('open');
			var aggregate = $(this).parent().data('load');
			popup.find('.text').html('');
			if (start != '' && end != '') {
				get_graphs($(this).parent().data('url') + 'separate/' + '?start=' + start + '&end=' + end, from, to);
			} else {
				get_graphs($(this).parent().data('url') + 'separate/', from, to);
			}
		}

		function get_bandwidth (callback) {
			$.getJSON(svgDiv.data('bandwidth-url'), function(data) {
				var bandwidth;
				for (item in data) {
					var $path = $('g[data-from="' + item.split('_')[0] + '"][data-to="' + item.split('_')[1] + '"]').find('path');
					bandwidth = data[item] / 1000000000;
					if (bandwidth > 5 && bandwidth < 15) {
						bandwidth = bandwidth * 0.7
					} else if (bandwidth > 15) {
						bandwidth = bandwidth * 0.5
					} else {
						bandwidth = bandwidth * 2
					}
					if (bandwidth === 0) {
						bandwidth = 1;
					}
					$path.attr('style', 'stroke-width: ' + bandwidth + '!important; stroke: #555555;');
					$path.on('click', show_details);
				}
				callback();
			})
		}


		function get_load(start, end) {
			var urlArgs = '';
			if ((start!=='') && (end!=='')) {
				urlArgs = '?start=' + start + '&end=' + end;
			}
			$('g').each(function () {
				if ($(this).data('load-url')) {
					var that = this;
					d3.json(d3.select(this).attr('data-url') + urlArgs, function (err, data) {
						if (!err && data.links.length) {
							var text;
							if (data.graph !== false) {
								text = '<h4>' + data.links[0].from + ' to ' + data.links[0].to + '</h4>' + '<img src="' + data.graph + '"/>'
							} else {
								text = '<h4>' + data.links[0].from + ' to ' + data.links[0].to + '</h4>' + '<p>No datasources found..</p>'
							}
							d3.select(that).attr('data-load', text);
						} else {
							d3.select(that).attr('data-load', 'Could not load data...');
						}
					});
				}
			});
		}

		function get_traffic (start, end) {
			var urlArgs = '';
			if ((start!=='') && (end!=='')) {
				urlArgs = '?start=' + start + '&end=' + end;
			}
			$.getJSON(svgDiv.data('load-url') + urlArgs, function(data) {
				var color;
				var bandwidth;
				for (item in data) {
					if (data[item].load !== undefined) {
						var $path = $('g[data-from="' + item.split('_')[0] + '"][data-to="' + item.split('_')[1] + '"]').find('path');
						bandwidth = data[item].bandwidth / 1000000000;
						if (bandwidth > 5 && bandwidth < 15) {
							bandwidth = bandwidth * 0.7
						} else if (bandwidth > 15) {
							bandwidth = bandwidth * 0.5
						} else {
							bandwidth = bandwidth * 2
						}

						var max_traffic = Math.round(Math.max(data[item].load['in'],data[item].load['out']));
						if (bandwidth === 0) {
							color = 'red';
							bandwidth = 1;
						} else {
							color = setColor(max_traffic);
						}
						$path.attr('style', 'stroke-width: ' + bandwidth + '!important; stroke:' + color);
						svgDiv.addClass('loaded');
						$('.updated').removeClass('hidden');
						$('.last-updated').text(moment().format('h:mm:ss'));
					}
					// everything is loaded now
					NProgress.done();
				}
				setTimeout(function (){
					svgDiv.removeClass('loaded');
				}, 100);
			});
		}

		var timespan = $('form#timespan');
		var start = timespan.find('#start');
		var end = timespan.find('#end');

		timespan.on('submit', function(ev) {
			ev.preventDefault();
			get_traffic(start.val(), end.val());
			get_load(start.val(), end.val());
		});

		$('#reportrange').daterangepicker({
		timePicker: true,
		timePickerIncrement: 30,
		format: 'MM/DD/YYYY h:mm A',
		ranges: {
			'Today': [moment().subtract(24, 'hours'), moment()],
			'Yesterday': [moment().subtract(2, 'days'), moment().subtract(1, 'days') ],
			'Last 7 Days': [moment().subtract(6, 'days'), moment()],
			'Last 30 Days': [moment().subtract(29, 'days'), moment()],
			'This Month': [moment().startOf('month'), moment().endOf('month')],
			'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
		},
			startDate: moment().subtract(29, 'days'),
			endDate: moment()
		},
		function(start, end) {
			$('#start').val(start.format('X'));
			$('#end').val(end.format('X'));
			get_traffic(start.format('X'), end.format('X'));
			$('#reportrange span').html(end.format('MMMM D, YYYY') + ' - ' + start.format('MMMM D, YYYY'));
			timespan.submit();
		});
		$('#reportrange span').html(moment().format('MMMM D, YYYY') + ' - ' + moment().subtract(24, 'hours').format('MMMM D, YYYY'));

		get_bandwidth(function () {
			setInterval(get_traffic(start.val(), end.val()), 5000);
			setInterval(get_load(start.val(), end.val()), 5000);

		});

		// add layers menu
		var ul = $('<ul class="layers"></ul>');
		for (var i=0; i < layers.length; i++) {
			ul.append($('<li>' + layers[i] + '</li>'));
		}
		svgDiv.prepend(ul);


		// toggle layers visibility
		$('ul.layers').on('click', 'li', function () {
			$(this).toggleClass('clicked');
			if ($("g[data-layer='" + $(this).text() + "']").css('display') === 'none') {
				$("g[data-layer='" + $(this).text() + "']").css({'display': ''});
			} else {
				$("g[data-layer='" + $(this).text() + "']").css({'display': 'none'});
			}
		});
	});
});

