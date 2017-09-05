import six
import json

from odoo import http
from odoo.http import request
import werkzeug.exceptions

from graphql import Source, execute, parse, validate
from graphql.execution import ExecutionResult

from odooku_graphql.schema import build_schema


class Graphql(http.Controller):

    @http.route('/graphql', type='http', auth="none")
    def index(self,  **kwargs):
        data = self._parse_body()
        batch = False
        query, variables, operation_name, id = self._get_graphql_params(data)
        source = Source(query, name='GraphQL request')
        execution_result = self._execute(source, variables, operation_name=operation_name)
        status = 200
        if execution_result:
            response = {}

            if execution_result.errors:
                response['errors'] = [self.format_error(e) for e in execution_result.errors]

            if execution_result.invalid:
                status = 400
            else:
                response['data'] = execution_result.data

            if batch:
                response['id'] = id
                response['status'] = status

            data = self.json_encode(request, response, pretty=show_graphiql)
        else:
            data = None

        return http.Response(data, status=status)


    def _parse_body(self, batch=False):
        content_type = request.httprequest.content_type
        if content_type == 'application/graphql':
            return {'query': request.body.decode()}

        elif content_type == 'application/json':
            try:
                body = request.body.decode('utf-8')
            except ValueError as e:
                raise werkzeug.exceptions.BadRequest(str(e)) 

            try:
                request_json = json.loads(body)
                if batch:
                    assert isinstance(request_json, list), (
                        'Batch requests should receive a list, but received {}.'
                    ).format(repr(request_json))
                    assert len(request_json) > 0, (
                        'Received an empty list in the batch request.'
                    )
                else:
                    assert isinstance(request_json, dict), (
                        'The received data is not a valid JSON query.'
                    )
                return request_json
            except AssertionError as e:
                raise werkzeug.exceptions.BadRequest(str(e))
            except (TypeError, ValueError):
                raise werkzeug.exceptions.BadRequest('POST body sent invalid JSON.')

        elif content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
            return request.POST

        return {}


    def _get_graphql_params(self, data):
        query = request.params.get('query')
        variables = request.params.get('variables')
        id = request.params.get('id')

        if variables and isinstance(variables, six.text_type):
            try:
                variables = json.loads(variables)
            except:
                raise ValueError('Variables are invalid JSON')

        operation_name = request.params.get('operationName') or data.get('operationName')
        if operation_name == "null":
            operation_name = None

        return query, variables, operation_name, id


    def _execute(self, source, variables, operation_name=None):
        schema = build_schema(request.env)
        try:
            document_ast = parse(source)
            validation_errors = validate(schema, document_ast)
            if validation_errors:
                return ExecutionResult(
                    errors=validation_errors,
                    invalid=True,
                )
        except Exception as e:
            return ExecutionResult(errors=[e], invalid=True)
        
        return execute(
            document_ast,
            variable_values=variables,
            operation_name=operation_name,
            context_value=request
        )
