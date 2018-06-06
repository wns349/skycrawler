$(document).ready(function () {
    var socket = io.connect("http://" + document.domain + ":" + location.port + "/flights");
    socket.on("response", function (msg) {
        console.log(msg);
    });

    socket.on("flight-info", function (msg) {
        console.log(msg);
    });

    $("form#new-flight").submit(function (event) {
        var origin = $("input[name='origin']").val();
        var destination = $("input[name='destination']").val();
        var departing = $("input[name='departing']").val();
        var returning = $("input[name='returning']").val();
        var id = origin + "-" + destination + "-" + departing + "-" + returning;
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