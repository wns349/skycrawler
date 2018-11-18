$(document).ready(function () {
    $("#start-date").datepicker({dateFormat: 'yy.mm.dd'});
    $("#end-date").datepicker({dateFormat: 'yy.mm.dd'});

    $("form#new-flight").submit(function (event) {
        event.preventDefault();

        var origin = $("input[name='origin']").val().toUpperCase();
        var destination = $("input[name='destination']").val().toUpperCase();
        var start_date = $("input[name='start-date']").val();
        var end_date = $("input[name='end-date']").val();
        var duration = $("select[name='duration']").val();
        var duration_text = $("select[name='duration'] :selected").text();
        var id = origin + destination + "_" + duration;

        var formData = new FormData();
        formData.append("origin", origin);
        formData.append("destination", destination);
        formData.append("start_date", start_date);
        formData.append("end_date", end_date);
        formData.append("duration", duration);
        formData.append("duration_text", duration_text);

        var divFlightInfo = $("div#" + id);
        $.ajax({
            url: "/api/flight/",
            type: "POST",
            data: formData,
            contentType: false,
            processData: false,
            success: function (result, status, xhr) {
                addFlightInfo(id, result);
            },
            error: function (xhr, status, error) {
                alert(status + "/" + error);
            }
        });

        window.scrollTo(0, document.body.scrollHeight);

        return false;
    });

});

function addFlightInfo(id, flightInfo) {
    var divFlightInfo = $("div#" + id);
    if (!divFlightInfo.length) {
        var template = $("#flight-info-template").html();
        divFlightInfo = $(template).clone();
        $(divFlightInfo).attr("id", id);
        $("div#flight-infos").append(divFlightInfo);
    }

    divFlightInfo.find("#close").click(function (e) {
        divFlightInfo.remove();
    });
    // header
    divFlightInfo.find("#origin-destination").text(flightInfo["origin"] + "-" + flightInfo["destination"]);
    divFlightInfo.find("#trip-duration").text(flightInfo["duration"]);

    // details
    divFlightInfo.find("#flight-details").empty();
    // add detail header
    $("<div class='row font-weight-bold'>" +
        "<div class='col-md-2'>출발-도착</div>" +
        "<div class='col-md-2'>Depart</div>" +
        "<div class='col-md-2'>Return</div>" +
        "<div class='col-md-2'>Expedia</div>" +
        "<div class='col-md-2'>Skyscanner</div>" +
        "<div class='col-md-2'>인터파크(국내선)</div>" +
        "</div>").appendTo(divFlightInfo.find("#flight-details"));

    // add detail
    $(flightInfo["details"]).each(function (idx, detail) {
        $("<div class='row'>" +
            "<div class='col-md-2'>" + flightInfo["origin"] + "-" + flightInfo["destination"] + "</div>" +
            "<div class='col-md-2'>" + detail["depart_date"] + "</div>" +
            "<div class='col-md-2'>" + detail["return_date"] + "</div>" +
            "<div class='col-md-2'><a href='" + detail["expedia"] + "' target='_blank'>Expedia</a></div>" +
            "<div class='col-md-2'><a href='" + detail["skyscanner"] + "' target='_blank'>Skyscanner</a></div>" +
            "<div class='col-md-2'><a href='" + detail["interpark_domestic"] + "' target='_blank'>인터파크(국내선)</a></div>" +
            "</div>").appendTo(divFlightInfo.find("#flight-details"));
    })
}
