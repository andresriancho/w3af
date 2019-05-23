# -*- coding: utf-8 -*-
from six import iteritems

from bravado_core.param import Param
from bravado_core.util import AliasKeyDict
from bravado_core.util import sanitize_name
from bravado_core import operation


def build_params_monkey_patch(op):
    """
    This is the monkey-patched version of build_params [0] for w3af.

    While parsing some open API specifications we found this error:

        The document at "http://moth/swagger.yaml" is not a valid Open API specification.
        The following exception was raised while parsing the dict into a specification object:
        "'Authorization' security parameter is overriding a parameter defined in operation
        or path object"

    And identified that the root cause for this "issue" was in this method.

    The problem was that we really needed to parse that specification, and we
    did not care that much about the restriction imposed by bravado-core.

    [0] https://github.com/Yelp/bravado-core/blob/1272d21b80800ad98d3f32c3aaa090e277466f69/bravado_core/operation.py#L153

    The following is the documentation for the original function:

    Builds up the list of this operation's parameters taking into account
    parameters that may be available for this operation's path component.

    :type op: :class:`bravado_core.operation.Operation`

    :returns: dict where (k,v) is (param_name, Param)
    """
    swagger_spec = op.swagger_spec
    deref = swagger_spec.deref
    op_spec = deref(op.op_spec)
    op_params_spec = deref(op_spec.get('parameters', []))
    spec_dict = deref(swagger_spec._internal_spec_dict)
    paths_spec = deref(spec_dict.get('paths', {}))
    path_spec = deref(paths_spec.get(op.path_name))
    path_params_spec = deref(path_spec.get('parameters', []))

    # Order of addition is *important* here. Since op_params are last in the
    # list, they will replace any previously defined path_params with the
    # same name when the final params dict is constructed in the loop below.
    params_spec = path_params_spec + op_params_spec

    params = AliasKeyDict()
    for param_spec in params_spec:
        param = Param(swagger_spec, op, deref(param_spec))
        sanitized_name = sanitize_name(param.name)
        params[sanitized_name] = param
        params.add_alias(param.name, sanitized_name)

    # Security parameters cannot override and been overridden by operation or path objects
    new_params = {}
    new_param_aliases = {}
    for parameter in op.security_parameters:
        param_name = sanitize_name(parameter.name)
        """
        Removed this code:
        
            if param_name in params:
                raise SwaggerSchemaError(
                    "'{0}' security parameter is overriding a parameter defined in operation or path object".format(
                        parameter.name,
                    )
                )
            else:
                # not directly in params because different security requirements could share parameters
                new_params[param_name] = parameter
                new_param_aliases[parameter.name] = param_name
        
        And replaced it with:
        """
        new_params[param_name] = parameter
        new_param_aliases[parameter.name] = param_name

    params.update(new_params)
    for alias, name in iteritems(new_param_aliases):
        params.add_alias(alias, name)
    return params


operation.build_params = build_params_monkey_patch
