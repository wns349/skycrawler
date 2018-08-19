from flask_restplus import Api
from .flight import api as api_flight

api = Api(
    title="Price checker",
    version="0.1",
    prefix="/api",
    doc="/api"
)
api.add_namespace(api_flight)