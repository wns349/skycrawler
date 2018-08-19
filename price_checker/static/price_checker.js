$(document).ready(function () {
    $("form#new-flight").submit(function (event) {
        event.preventDefault();

        var origin = $("input[name='origin']").val().toUpperCase();
        var destination = $("input[name='destination']").val().toUpperCase();
        var base_date = $("input[name='base-date']").val();
        var returning = $("input[name='returning']").val();
        var before = $("input[name='base-date-before']").val();
        var after = $("input[name='base-date-after']").val();
        var id = origin + destination + base_date.replace(/\./g, "") + returning + "_" + before + "_" + after;
        console.log("id: " + id);

        // var formData = $(this).serialize();

        var formData = new FormData();
        formData.append("origin", origin);
        formData.append("destination", destination);
        formData.append("base_date", base_date);
        formData.append("returning", returning);
        formData.append("before", before);
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
                    console.log(result);
                    console.log(status);
                    console.log(xhr);
                },
                error: function (xhr, status, error) {
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
