$(document).ready(function () {
    $("form#new-flight").submit(function (event) {
        event.preventDefault();

        var origin = $("input[name='origin']").val().toUpperCase();
        var destination = $("input[name='destination']").val().toUpperCase();
        var base_date = $("input[name='base-date']").val();
        var returning = $("input[name='returning']").val();
        var after = $("input[name='base-date-after']").val();
        var id = origin + destination + base_date.replace(/\./g, "") + returning + "_" + after;

        var formData = new FormData();
        formData.append("origin", origin);
        formData.append("destination", destination);
        formData.append("base_date", base_date);
        formData.append("returning", returning);
        formData.append("after", after);

        var divFlightInfo = $("div#" + id);
        if (divFlightInfo.length) {
            document.getElementById(id).scrollIntoView();
        } else {
            $.ajax({
                url: "/api/flight/",
                type: "POST",
                //contentType: "application/x-www-form-urlencoded",
                data: formData,
                contentType: false,
                processData: false,
                success: function (result, status, xhr) {
                    // $("#flash").hide();
                    addFlightInfo(id, result);
                },
                error: function (xhr, status, error) {
                    // $("#flash").text(error);
                    // $("#flash").show();
                    console.log(xhr);
                    console.log(status);
                    console.log(error);
                }
            });

            window.scrollTo(0, document.body.scrollHeight);
        }

        return false;
    });

});

function addFlightInfo(id, flightInfo) {
    console.log(flightInfo);
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

    // details
    $(flightInfo["details"]).each(function (idx, detail) {
        $("<div class='row'>" +
            "<div class='col-md-2'>" + flightInfo["origin"] + "-" + flightInfo["destination"] + "</div>" +
            "<div class='col-md-3'>" + detail["depart_date"] + "</div>" +
            "<div class='col-md-3'>" + detail["return_date"] + "</div>" +
            "<div class='col-md-2'><a href='" + detail["expedia"] + "' target='_blank'>Expedia</a></div>" +
            "<div class='col-md-2'><a href='" + detail["skyscanner"] + "' target='_blank'>Skyscanner</a></div>" +
            "</div>").appendTo(divFlightInfo.find("#flight-details"));
    })
}
