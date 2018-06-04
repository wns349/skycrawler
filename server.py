from flask import Flask

temp = {}
temp["id"] = "0"
temp["route"] = "ICN - NRT"
temp["date"] = "2018.06.23 - 2018.06.30"
temp["flights"] = []
temp["flights"].append({
    "airline": "이스타항공",
    "time": "16:00 - 16:30",
    "price": "132000"
})
temp["updated"] = "2018.06.11 14:00"
flight_infos = {"0": temp}

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="helloworld1234"
    )

    import controller
    app.register_blueprint(controller.bp)
    app.add_url_rule('/', endpoint='index')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
