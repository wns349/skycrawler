function addFlightInfo(id, flightInfo, refreshFlightInfo, deleteFlightInfo) {
    console.log(flightInfo);
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
    divFlightInfo.find("#close").click(function (e) {
        deleteFlightInfo(id);
    });
    divFlightInfo.find("#refresh").click(function (e) {
        refreshFlightInfo(id);
    });

    if (flightInfo["error"] == undefined && flightInfo["flights"].length) {
        divFlightInfo.find("#flights-available").show();
        divFlightInfo.find("#flights-not-available").hide();
        divFlightInfo.find("#flights").empty();
        $.each(flightInfo["flights"], function (i, flight) {
            var li = $("<li>");
            li.text(flight["depart"] + "\t" + flight["return"] + "\t" + flight["airline"] + "\t" + flight["price"]);
            // li.text(flight["airline"] + "\t" + flight["depart"] + "\t" + flight["return"] + "\t" + flight["price"]);
            if (flight["airline"] == "이스타항공") {
                li.attr("class", "eastar");
            }
            divFlightInfo.find("#flights").append(li);
        });
        divFlightInfo.find("#external-link-expedia").attr("href", flightInfo["url"]["expedia"]);
        divFlightInfo.find("#external-link-skyscanner").attr("href", flightInfo["url"]["skyscanner"]);
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
    var socket = io.connect("http://" + document.domain + ":" + location.port + "/flights", {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: 99999
    });
    var deleteFlightInfo = function (id) {
        socket.emit("delete", {
            id: id
        });

        if ($("div#" + id).length) {
            $("div#" + id).remove();
        }
    }
    var refreshFlightInfo = function (id) {
        socket.emit("refresh", {
            id: id
        });
        if ($("div#" + id).length) {
            var divFlightInfo = $("div#" + id);
            divFlightInfo.find("#flights-available").hide();
            divFlightInfo.find("#flights-not-available").show();
        }
    }

    socket.on("response", function (msg) {
        var flightInfos = msg["data"]
        $.each(flightInfos, function (key, value) {
            addFlightInfo(key, value, refreshFlightInfo, deleteFlightInfo);
        });
    });

    socket.on("flight-info", function (msg) {
        addFlightInfo(msg["data"]["id"], msg["data"], refreshFlightInfo, deleteFlightInfo);
    });

    $("form#new-flight").submit(function (event) {
        var origin = $("input[name='origin']").val().toUpperCase();
        var destination = $("input[name='destination']").val().toUpperCase();
        var departing = $("input[name='departing']").val();
        var returning = $("input[name='returning']").val();
        var id = origin + destination + departing.replace(/\./g, "") + returning.replace(/\./g, "");

        var divFlightInfo = $("div#" + id);
        if (divFlightInfo.length) {
            document.getElementById(id).scrollIntoView();
        } else {
            socket.emit("request", {
                id: id,
                origin: origin,
                destination: destination,
                departing: departing,
                returning: returning
            });

            window.scrollTo(0, document.body.scrollHeight);
        }

        return false;
    });
});