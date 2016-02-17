function loadChart(picker, i) {
    var start = picker.startDate.format('DD/MM/YYYY');
    var numdays = Math.round((picker.endDate - picker.startDate)/(24 * 60 * 60 * 1000));
    var url = "/distanceVsDay?imei=" + i+ "&s=" + start + "&nd=" + numdays;
    $.ajax({
    url: url
    }).success(function(data) {

        $('#container').highcharts({
            credits: {
                enabled: false
            },
            chart: {
              type: 'column',
              zoomType: 'x'
            },
            title: {
                text: 'Distance Travelled per Day'
            },
            xAxis: {
                categories: data.xAxis
            },
            yAxis: {
                min: 0,
                title: {
                    text: 'Distance in km'
                }
            },
            legend: {
                reversed: true
            },
            plotOptions: {
                series: {
                    stacking: 'normal'
                }
            },
            series: [{
                name: 'CDF',
                data: data.cummulative,
                color: '#c3c6c0',
                visible: false
              },
              {
                name: 'Distance per day',
                data: data.distance
            }]
        });

        // Set average distance
        $('#distance').text(Math.round(data.average) + " km");
    });
}