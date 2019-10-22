"""
example_specifications.py

Copyright 2018 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import json
import os

from apispec import APISpec
from flask import Flask, jsonify
from marshmallow import Schema, fields

CURRENT_PATH = os.path.split(__file__)[0]


class IntParamQueryString(object):
    def get_specification(self):
        return file('%s/data/int_param_qs.json' % CURRENT_PATH).read()


class StringParamJson(object):
    def get_specification(self):
        return file('%s/data/string_param_json.json' % CURRENT_PATH).read()


class IntParamJson(object):
    def get_specification(self):
        return file('%s/data/int_param_json.json' % CURRENT_PATH).read()


class IntParamWithExampleJson(object):
    def get_specification(self):
        return file('%s/data/int_param_with_example_json.json' % CURRENT_PATH).read()


class IntParamNoModelJson(object):
    def get_specification(self):
        return file('%s/data/int_param_no_model_json.json' % CURRENT_PATH).read()


class ComplexDereferencedNestedModel(object):
    def get_specification(self):
        return file('%s/data/complex_dereferenced_nested_model.json' % CURRENT_PATH).read()


class DereferencedPetStore(object):
    def get_specification(self):
        return file('%s/data/dereferenced_pet_store.json' % CURRENT_PATH).read()


class NestedModel(object):
    def get_specification(self):
        return file('%s/data/nested_model.json' % CURRENT_PATH).read()


class NestedLoopModel(object):
    def get_specification(self):
        return file('%s/data/nested_loop_model.json' % CURRENT_PATH).read()


class StringParamHeader(object):
    def get_specification(self):
        return file('%s/data/string_param_header.json' % CURRENT_PATH).read()


class MultiplePathsAndHeaders(object):
    def get_specification(self):
        return file('%s/data/multiple_paths_and_headers.json' % CURRENT_PATH).read()


class PetstoreSimpleModel(object):

    @staticmethod
    def get_specification():
        return file('%s/data/petstore-simple.json' % CURRENT_PATH).read()


class IntParamPath(object):
    def get_specification(self):
        spec = APISpec(
            title=self.__class__.__name__,
            version='1.0.0',
            plugins=(
                'apispec.ext.flask',
                'apispec.ext.marshmallow',
            ),
        )

        class PetParameter(Schema):
            pet_id = fields.Int()

        class PetSchema(Schema):
            id = fields.Int()
            name = fields.Str()

        app = Flask(__name__)

        @app.route('/pets/<int:pet_id>')
        def get_pet(pet_id):
            """A cute furry animal endpoint.
            ---
            get:
                description: Get a random pet
                parameters:
                    - in: path
                      schema: PetParameter
                responses:
                    200:
                        description: A pet to be returned
                        schema: PetSchema
            """
            return jsonify({})

        # Register entities and paths
        spec.definition('Pet', schema=PetSchema)
        spec.definition('PetParameter', schema=PetParameter, required=True)
        with app.test_request_context():
            spec.add_path(view=get_pet)

        specification_as_string = json.dumps(spec.to_dict(), indent=4)

        # Kludge! I was unable to do this via `apispec`
        specification_as_string = specification_as_string.replace('"required": false,',
                                                                  '"required": true,')

        return specification_as_string


class StringParamQueryString(object):
    def get_specification(self):
        return file('%s/data/string_param_qs.json' % CURRENT_PATH).read()


class ArrayStringItemsQueryString(object):
    def get_specification(self):
        return file('%s/data/array_string_items_qs.json' % CURRENT_PATH).read()


class ArrayIntItemsQueryString(object):
    def get_specification(self):
        return file('%s/data/array_int_items_qs.json' % CURRENT_PATH).read()


class ArrayModelItems(object):
    def get_specification(self):
        return file('%s/data/array_model_items_json.json' % CURRENT_PATH).read()


class NoParams(object):

    def get_specification(self):
        spec = APISpec(
            title=self.__class__.__name__,
            version='1.0.0',
            plugins=(
                'apispec.ext.flask',
                'apispec.ext.marshmallow',
            ),
        )

        class PetSchema(Schema):
            id = fields.Int()
            name = fields.Str()

        app = Flask(__name__)

        @app.route('/random')
        def random_pet():
            """A cute furry animal endpoint.
            ---
            get:
                description: Get a random pet
                responses:
                    200:
                        description: A pet to be returned
                        schema: PetSchema
            """
            return jsonify({})

        # Register entities and paths
        spec.definition('Pet', schema=PetSchema)
        with app.test_request_context():
            spec.add_path(view=random_pet)

        return json.dumps(spec.to_dict(), indent=4)


class ModelParam(object):

    def get_specification(self):
        spec = APISpec(
            title=self.__class__.__name__,
            version='1.0.0',
            plugins=(
                'apispec.ext.flask',
                'apispec.ext.marshmallow',
            ),
        )

        class PetSchema(Schema):
            id = fields.Int()
            name = fields.Str()

        app = Flask(__name__)

        @app.route('/random')
        def random_pet():
            """A cute furry animal endpoint.
            ---
            get:
                description: Get a random pet
                responses:
                    200:
                        description: A pet to be returned
                        schema: PetSchema
            """
            return jsonify({})

        # Register entities and paths
        spec.definition('Pet', schema=PetSchema)
        with app.test_request_context():
            spec.add_path(view=random_pet)

        return json.dumps(spec.to_dict(), indent=4)


class ModelParamNested(object):

    def get_specification(self):
        spec = APISpec(
            title=self.__class__.__name__,
            version='1.0.0',
            plugins=(
                'apispec.ext.flask',
                'apispec.ext.marshmallow',
            ),
        )

        class CategorySchema(Schema):
            id = fields.Int()
            name = fields.Str(required=True)

        class PetSchema(Schema):
            category = fields.Nested(CategorySchema, many=True)
            name = fields.Str()

        app = Flask(__name__)

        @app.route('/random')
        def random_pet():
            """A cute furry animal endpoint.
            ---
            get:
                description: Get a random pet
                responses:
                    200:
                        description: A pet to be returned
                        schema: PetSchema
            """
            return jsonify({})

        # Register entities and paths
        spec.definition('Category', schema=CategorySchema)
        spec.definition('Pet', schema=PetSchema)
        with app.test_request_context():
            spec.add_path(view=random_pet)

        return json.dumps(spec.to_dict(), indent=4)


class ModelParamNestedLoop(object):

    def get_specification(self):
        spec = APISpec(
            title=self.__class__.__name__,
            version='1.0.0',
            plugins=(
                'apispec.ext.flask',
                'apispec.ext.marshmallow',
            ),
        )

        class A(Schema):
            id = fields.Int()
            pointers = fields.Nested('B', many=True)

        class B(Schema):
            id = fields.Int()
            pointers = fields.Nested('C', many=True)

        class C(Schema):
            id = fields.Int()
            pointers = fields.Nested('A', many=True)

        app = Flask(__name__)

        @app.route('/random')
        def random_pet():
            """A cute furry animal endpoint.
            ---
            get:
                description: Get a random pet
                responses:
                    200:
                        description: A pet to be returned
                        schema: PetSchema
            """
            return jsonify({})

        # Register entities and paths
        spec.definition('A', schema=A)
        spec.definition('B', schema=B)
        spec.definition('C', schema=C)
        with app.test_request_context():
            spec.add_path(view=random_pet)

        return json.dumps(spec.to_dict(), indent=4)
