function addFlightInfo(id, flightInfo, deleteFlightInfo) {
    if (flightInfo["deleted"]) {
        return;
    }

    var divFlightInfo = $("div#" + id);
    if (!divFlightInfo.length) {
        var template = $("#flight-info-template").html();
        divFlightInfo = $(template).clone();
        $(divFlightInfo).attr("id", id);
        $("div#flight-infos").append(divFlightInfo);
    }

    divFlightInfo.find("#origin-destination").text(flightInfo["origin"] + "-" + flightInfo["destination"]);
    divFlightInfo.find("#dates").text(flightInfo["departing"] + "-" + flightInfo["returning"]);

    if (flightInfo["error"] == undefined && flightInfo["flights"].length) {
        divFlightInfo.find("#flights-available").show();
        divFlightInfo.find("#flights-not-available").hide();
        divFlightInfo.find("#flights").empty();
        $.each(flightInfo["flights"], function (i, flight) {
            var li = $("<li>");
            li.text(flight["time"] + "\t" + flight["airline"] + "\t" + flight["price"]);
            divFlightInfo.find("#flights").append(li);
        });

        divFlightInfo.find("#close").click(function (e) {
            deleteFlightInfo(id);
        });
        divFlightInfo.find("#external-link").attr("href", flightInfo["url"]);
        divFlightInfo.find("#updated_at").text(new Date(flightInfo["updated_at"]));
    } else {
        divFlightInfo.find("#flights-available").hide();
        divFlightInfo.find("#flights-not-available").show();
        if (flightInfo["error"] == undefined) {
            divFlightInfo.find("#error").text("Loading...");
        } else {
            divFlightInfo.find("#error").text("ERROR: " + flightInfo["error"]);
        }
    }
};


$(document).ready(function () {
    var socket = io.connect("http://" + document.domain + ":" + location.port + "/flights");
    var deleteFlightInfo = function (id) {
        socket.emit("delete", {
            id: id
        });

        if ($("div#" + id).length) {
            $("div#" + id).remove();
        }
    }

    socket.on("response", function (msg) {
        var flightInfos = msg["data"]
        $.each(flightInfos, function (key, value) {
            addFlightInfo(key, value, deleteFlightInfo);
        });
    });

    socket.on("flight-info", function (msg) {
        addFlightInfo(msg["data"]["id"], msg["data"], deleteFlightInfo);
    });

    $("form#new-flight").submit(function (event) {
        var origin = $("input[name='origin']").val();
        var destination = $("input[name='destination']").val();
        var departing = $("input[name='departing']").val();
        var returning = $("input[name='returning']").val();
        var id = origin + destination + departing.replace(/\./g, "") + returning.replace(/\./g, "");
        socket.emit("request", {
            id: id,
            origin: origin,
            destination: destination,
            departing: departing,
            returning: returning
        });

        return false;
    });
});