$(function(){
   	var networkLoadDiv = $('#network-load');
   	if (networkLoadDiv.length) {
        var initialized = false;

	    function updateChart(max3) {
            for (var i=0; i < max3.length; i++) {
                if (initialized) {
                    var chart = $('#container-network .gauge' + i);
                    var point = chart.series[0].points[0];
                    point.update(parseFloat(max3[i].load.toFixed(1)))
                    
                } else {
                    var gaugeOptions = {
                        chart: {
                            type: 'solidgauge'
                        },
                        title: max3[i].name,
                        pane: {
                            center: ['50%', '85%'],
                            size: '140%',
                            startAngle: -90,
                            endAngle: 90,
                            background: {
                                backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                                innerRadius: '60%',
                                outerRadius: '100%',
                                shape: 'arc'
                            }
                        },
                        tooltip: {
                            enabled: false
                        },
                        // the value axis
                        yAxis: {
                            stops: [
                                [0.2, '#55BF3B'], // green
                                [0.5, '#DDDF0D'], // yellow
                                [0.8, '#DF5353'] // red
                            ],
                            lineWidth: 0,
                            minorTickInterval: null,
                            tickPixelInterval: 400,
                            tickWidth: 0,
                            title: {
                                y: -70
                            },
                            labels: {
                                y: 16
                            }
                        },

                        plotOptions: {
                            solidgauge: {
                                dataLabels: {
                                    y: 5,
                                    borderWidth: 0,
                                    useHTML: true
                                }
                            }
                        }
                    };
                    $('#container-network .gauge' + i).highcharts(Highcharts.merge(gaugeOptions, {
                        yAxis: {
                            min: 0,
                            max: 100,
                            title: {
                                text: max3[i].name
                            }
                        },

                        credits: {
                            enabled: false
                        },

                        series: [{
                            name: 'load',
                            data: [parseFloat(max3[i].load.toFixed(1))],
                            dataLabels: {
                                format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                                    ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '"> {y}%</span>'
                            },
                        }]

                    }));
                }
            }
            initialized = true;
	    }

	    function getLoad() {
	    	var total = 0;
	   		$.get(networkLoadDiv.data('url'), function(data) {
                var load = [];
	   			for (link in data) {
                    var obj = {'name': link, 'load':  data[link].load.out};
                    load.push(obj);
	   			}
                var max = _.sortBy(load, 'load').reverse().slice(0,3);
                updateChart(max);
	   		});
	    }
        getLoad(); 
        setInterval(function () {
            getLoad();
        }, 60000);
   	}
});
