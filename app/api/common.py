from flask_restful import Resource
from app.models import Department
from app.api import api

class Departments(Resource):
    def get(self):
        depts = Department.query.order_by(Department.name).all()
        return {
            'departments': [{
                'id': d.id,
                'name': d.name,
                'description': d.description
            } for d in depts]
        }

api.add_resource(Departments, '/departments')
