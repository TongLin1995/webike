/* Trips Chart */
function loadChart(picker, i) {
    var start = picker.startDate.format('MM/DD/YYYY');
    var numdays = Math.round((picker.endDate - picker.startDate)/(24 * 60 * 60 * 1000));
    var url = "/webike/distanceVsDay?imei=" + i+ "&s=" + start + "&nd=" + numdays;
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

/* Trips Google Map */
var colors = ["#504B4B", "#00FF00", "#0000FF", "#000000", "#FFFF00", "#00FFFF", "#FF00FF", "#FFE4C4", "#A52A2A", "#5F9EA0", "#FF7F50", "#DC143C", "#008B8B", "#B8860B", "#BDB76B", "#556B2F", "#483D8B", "#1E90FF"];
function mapTrips(datatable, picker, imei) {

    $('#trips-container').hide();
    $('.dots-loader').css("display", "block");

    var date = picker.startDate.format('MM/DD/YYYY');
    var url = "/webike/tripCoords?imei=" + imei + "&date=" + date;

    $.ajax({
        url: url
    }).success(function(data) {

        $('.dots-loader').hide();
        $('#trips-container').show();
        datatable.clear(); // remove all data from table

        // init map
        var mapOptions = {
          zoom: 15,
          mapTypeId: google.maps.MapTypeId.TERRAIN
        };

        var map = new google.maps.Map(document.getElementById('trips-container'), mapOptions);

        var markers = [];

        // populate lats and longs
        var numTrips = data.stamps.length
        var lats = data.lats;
        var longs = data.longs;

        var centerLat = 43.472285;
        var centerLong = -80.544858;
        var bounds = new google.maps.LatLngBounds();

        for (var k = 0; k < numTrips; k++) {
            var flightPlanCoordinates = [];
            var len = lats[k].length - 1;
            for (var i = 0; i < len; i++) {
                flightPlanCoordinates.push(new google.maps.LatLng(lats[k][i], longs[k][i]));

                // set bounds
                bounds.extend(new google.maps.LatLng(lats[k][i], longs[k][i]));
                map.fitBounds(bounds);
            }

            var flightPath = new google.maps.Polyline({
                path: flightPlanCoordinates,
                geodesic: true,
                strokeColor: colors[k],
                strokeOpacity: 1.0,
                strokeWeight: 2
            });

            flightPath.setMap(map);

            // Start of trip
            markers.push(new google.maps.Marker({
               position: new google.maps.LatLng(lats[k][0], longs[k][0]),
               map: map,
               title:'Start of Trip #' + (k+1)
            }));

            // End of trip
            markers.push(new google.maps.Marker({
               position: new google.maps.LatLng(lats[k][len-1], longs[k][len-1]),
               map: map,
               title:'End of Trip #' + (k+1)
            }));
        }

        // tables
        var tableRows = [];
        var tripId = data.tripIDs;
        var startTime = data.start;
        var endTime   = data.end;
        var tt        = data.ttime;
        var distance  = data.d;
        var isAccurate = data.isAccurate;
        var comments  = data.comments;

        for (var i = 0; i < numTrips; i++) {
            tableRows.push([
                tripId[i], 
                startTime[i], 
                endTime[i], 
                tt[i].toFixed(2), 
                distance[i].toFixed(2), 
                isAccurate[i], 
                comments[i],
                null
                ]);
        }

        datatable.rows.add(tableRows).draw();
      });

}

function addClickToSave(imei, datatable) {

    $('.btn-save-datatable').click(function(){

        var $btn = $(this).button('loading')
        var tripID = $btn.attr("data")
        var $isAccurate = $('#isAccurate_' + tripID);
        var $comment = $('#comment_' + tripID);

        var tr = $(this).closest('tr');
        var rowIndex = datatable.row( tr[0] ).index();
        
        var url = "/webike/updateTripComments";

        var jqxhr = $.post( url, { imei: imei, id: tripID, isAccurate: $isAccurate.prop('checked'), comment: $comment.val() })
          .done(function() {
            datatable.cell(rowIndex, 5).data($isAccurate.prop('checked')).draw();
            datatable.cell(rowIndex, 6).data($comment.val()).draw();
          })
          .fail(function() {
            alert( "Failed to update the trip info." );
          });

        return false;
    });

}

/* SOC Estimation Chart */
function loadSOCChart(picker, i) {

    $('#soc-container').hide();
    $('.dots-loader').css("display", "block");

    Highcharts.setOptions({
        global: {
            timezoneOffset: 4 * 60
        }
    });

    var start = picker.startDate.format('MM/DD/YYYY');
    var numdays = Math.round((picker.endDate - picker.startDate)/(24 * 60 * 60 * 1000));
    var url = "/webike/socEstimation?imei=" + i+ "&s=" + start + "&nd=" + numdays;
    $.ajax({
        url: url
    }).success(function(data) {

        $('.dots-loader').hide();
        $('#soc-container').show();

        // Create the chart
        $('#soc-container').highcharts('StockChart', {
            credits: {
                enabled: false
            },
            rangeSelector: {
                enabled: false
            },
            yAxis: {
                title: {
                    text: 'SOC Estimation (%)'
                }
            },

            series: [{
                name: 'Temperature',
                data: data.yAxis
            }]
        // Set average distance
        //$('#distance').text(Math.round(data.average) + " km");
        });
    });
}
