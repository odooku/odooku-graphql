import six
import json
import re
import jinja2

from odoo import http
from odoo.http import request
import werkzeug.exceptions

from graphql import Source, execute, parse, validate
from graphql.execution import ExecutionResult
from graphql.error import (
    GraphQLError,
    format_error as format_graphql_error
)

from odooku_graphql.schema import build_schema
from odooku_addons.odooku_graphql.utils.html import escapejs


GRAPHIQL_VERSION = '0.10.2'


def get_graphql_params(data):
    query = request.params.get('query') or data.get('query')
    variables = request.params.get('variables') or data.get('variables')
    id_ = request.params.get('id') or data.get('id')

    if variables and isinstance(variables, six.text_type):
        try:
            variables = json.loads(variables)
        except:
            raise ValueError('Variables are invalid JSON')

    operation_name = request.params.get('operationName') or data.get('operationName')
    if operation_name == "null":
        operation_name = None

    return query, variables, operation_name, id_


def get_accepted_content_types():
    def qualify(x):
        parts = x.split(';', 1)
        if len(parts) == 2:
            match = re.match(r'(^|;)q=(0(\.\d{,3})?|1(\.0{,3})?)(;|$)',
                             parts[1])
            if match:
                return parts[0], float(match.group(2))
        return parts[0], 1

    raw_content_types = request.httprequest.headers.get('accept', '*/*').split(',')
    qualified_content_types = map(qualify, raw_content_types)
    return list(x[0] for x in sorted(
        qualified_content_types,
        key=lambda x: x[1], reverse=True)
    )


def json_encode(data, pretty=False):
    if pretty or request.params.get('pretty'):
        return json.dumps(data, separators=(',', ':'))

    return json.dumps(data, sort_keys=True, indent=2, separators=(',', ': '))


def format_as_graphql_error(error):
    if isinstance(error, GraphQLError):
        return format_graphql_error(error)

    return {'message': six.text_type(error)}


def parse_body(batch=False):
    content_type = request.httprequest.content_type
    if content_type == 'application/graphql':
        return {'query': request.httprequest.get_data().decode()}

    elif content_type == 'application/json':
        try:
            body = request.httprequest.get_data().decode('utf-8')
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
        
        return body
    elif content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
        return request.POST

    return {}


def is_raw(data):
    return 'raw' in request.params or 'raw' in data


def wants_html():
    accepted = get_accepted_content_types()
    html_index = accepted.count('text/html')
    json_index = accepted.count('application/json')
    return html_index > json_index


def execute_graphql(source, variables, operation_name=None):
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

loader = jinja2.PackageLoader('odooku_addons.odooku_graphql', 'templates')
env = jinja2.Environment(loader=loader, autoescape=True)
env.filters['escapejs'] = escapejs

class Graphql(http.Controller):
    
    @http.route('/graphql', type='http', csrf=False, auth="none")
    def index(self,  **kwargs):
        data = parse_body()
        batch = False
        show_graphiql = not is_raw(data) and wants_html()
        query, variables, operation_name, id_ = get_graphql_params(data)
        if show_graphiql:
            template = env.get_template('graphiql.html')
            return template.render({
                'graphiql_version': GRAPHIQL_VERSION,
                'query': query or '',
                'variables': json.dumps(variables) or '',
                'operation_name': operation_name or ''
            })

        if query is None:
            raise werkzeug.exceptions.BadRequest('Must provide query string.')

        source = Source(query, name='GraphQL request')
        execution_result = execute_graphql(source, variables, operation_name=operation_name)

        status = 200
        if execution_result:
            data = {}
            if execution_result.errors:
                data['errors'] = [format_as_graphql_error(e) for e in execution_result.errors]

            if execution_result.invalid:
                status = 400
            else:
                data['data'] = execution_result.data

            if batch:
                data['id'] = id
                data['status'] = status

            data = json_encode(data, pretty=show_graphiql)
        else:
            data = None

        return http.Response(data, status=status)
