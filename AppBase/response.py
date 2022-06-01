# -*- coding: utf-8 -*-

import base64
import functools
import json
import os
import time

from cryptography.fernet import Fernet
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from traceback_with_variables import iter_exc_lines

from .tools import gen_template_name, check_for_template

tmplIncs = []

# Define Status codes here
SUCCESSFUL_RESPONSE = 200
SUCCESSFUL_RESPONSE_WITHOUT_OUTPUT = 204
ERROR_RESPONSE = 103
ERROR_RESPONSE_WITHOUT_OUTPUT = 104
UNAUTHORIZED_ACCESS = 401
FORBIDDEN_REQUEST = 403

# piece types
PIECE_AS_RESPONSE = 1
PIECE_AS_STRING = 2

"""
@description        decorator method for sending a web html response
@param  pageTitle   @nullable string        page title
@param  tmpl        @nullable string        name of template without ".html", if not available uses gen_template_name
"""


def encrypt(func):
    class CustomRequest:
        META = {}
        body = b''

        def __init__(self, req, body):
            self.META = req.META.copy()
            self.body = body

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        original_req = args[0]

        try:
            encryption_key_p1 = original_req.META["HTTP_API_KEY"]
            encryption_key_p2 = original_req.META["HTTP_ACCESS_TOKEN"]
        except:
            return JsonResponse({'message': 'encryption error', 'data': list(original_req.META.keys())}, status=403)

        try:
            encoding_language = encryption_key_p1 + encryption_key_p2
            encoding_language = base64.urlsafe_b64encode(encoding_language[0:64:2].encode())
            fernet_encrypt = Fernet(encoding_language)
            decoded_req = CustomRequest(original_req, fernet_encrypt.decrypt(original_req.body))
        except:
            return JsonResponse({'message': 'encryption error'}, status=401)

        http_response = func(decoded_req)
        status = http_response.status_code
        response_body = http_response.content

        try:
            encoded_data = fernet_encrypt.encrypt(response_body)
            return HttpResponse(content=encoded_data, status=status)
        except:
            return JsonResponse({'message': 'encryption error'}, status=502)

    return wrapper


REQUEST_ID = get_random_string(length=32)


def usage(_func=None, *, request_skip=None, response_skip=None, service='default', additional_param='',
          middleware=None):
    if response_skip is None:
        response_skip = []

    if request_skip is None:
        request_skip = []

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):

            if wrapper.service == 'default':
                wrapper.service = settings.USAGE_APP_NAME
                wrapper.usage.app = settings.USAGE_APP_NAME

            wrapper.start_time = time.perf_counter()

            # handle request - start
            try:
                if args[0].__class__.__name__ not in ['WSGIRequest', 'CustomRequest']:
                    raise IndexError

                try:
                    wrap_json_request(json.loads(args[0].body.decode('utf-8')), args[0])
                except json.JSONDecodeError:
                    wrap_http_response(args, kwargs)

            except IndexError:
                wrap_internal_request(args, kwargs)
            # handle request - end

            # handle response - start
            try:
                function_response = function(*args, **kwargs)
                try:
                    response_body, status, _ = detect_response_type(function_response)
                    wrap_json_response(response_body, status)
                except ValueError:
                    response_type = function_response.__class__.__name__
                    if response_type in ['HttpResponse', 'JsonResponse']:
                        try:
                            wrap_json_response(json.loads(function_response.content), function_response.status_code)
                        except json.JSONDecodeError:
                            wrap_http_response(function_response.content, function_response.status_code)
                    else:
                        wrapper.usage.response = 'unknown response type'
                        wrapper.usage.status = 507

            except Exception as e:
                function_response = HttpResponse(content=str(e) + '\n' + '\n'.join(list(iter_exc_lines(e))), status=500)
                wrapper.usage.response = str(e) + '\n' + '\n'.join(list(iter_exc_lines(e)))
                wrapper.usage.status = 500

            # handle response - end

            wrapper.end_time = time.perf_counter()
            wrapper.usage.duration = wrapper.end_time - wrapper.start_time
            if wrapper.middleware:
                [request_body, response_body, command, status] = wrapper.middleware(
                    wrapper.usage.request,
                    wrapper.usage.response,
                    wrapper.usage.command,
                    wrapper.usage.status
                )

                wrapper.usage.request = request_body
                wrapper.usage.response = response_body
                wrapper.usage.command = command
                wrapper.usage.status = status

            # skip successful requests
            # if wrapper.usage.status == 200 and not settings.DEBUG: @TODO Uncomment this
            #     wrapper.usage.response = {}

            try:
                wrapper.usage.save()
            except Exception as _:
                pass

            return function_response

        def wrap_json_request(request_body, req):
            for item in wrapper.request_skip:
                if item in request_body.keys():
                    request_body[item] = "[private]"

            if 'request' in request_body.keys():
                wrapper.usage.command = request_body['request']

            try:
                request_headers = {}
                for name, header_value in req.META.items():
                    if type(header_value) is str and name.startswith("HTTP_"):
                        request_headers[name] = "[private]" if name in wrapper.request_skip else header_value
            except Exception as e:
                request_headers = {
                    'message': 'cannot resolve headers',
                    'error': str(e) + '\n' + '\n'.join(list(iter_exc_lines(e)))
                }

            wrapper.usage.request = {
                'body': request_body,
                'headers': request_headers
            }

            wrapper.usage.save()

        def wrap_json_response(response_body, status):
            wrapper.usage.response = response_body
            wrapper.usage.status = status

        def wrap_internal_request(*args, **kwargs):
            try:
                wrapper.usage.request = {
                    'kwargs': dict(kwargs),
                    'args': [str(x) for x in args]
                }
            except Exception as e:
                wrapper.usage.response = str(e) + '\n' + '\n'.join(list(iter_exc_lines(e)))
                wrapper.usage.status = 506
                wrapper.usage.save()

        def wrap_http_response(*args, **kwargs):
            pass

        wrapper.request_skip = request_skip
        wrapper.response_skip = response_skip
        wrapper.service = service
        wrapper.additional_param = additional_param
        wrapper.middleware = middleware
        wrapper.start_time = 0
        wrapper.end_time = 0

        from Platform.models import Usage
        wrapper.usage = Usage(
            app=wrapper.service,
            additional_param=wrapper.additional_param,
            status=504,
            command=function.__name__,
        )

        return wrapper

    if _func:
        return decorator(_func)

    return decorator


def html(method=None):
    if method is None:
        return functools.partial(html)

    @functools.wraps(method)
    def f(*args, **kwargs):
        res = method(*args, **kwargs)
        [data, status_code, buff] = detect_response_type(res)
        r = HttpResponse()

        if type(buff) is dict:
            if 'redirect' in buff.keys():
                r["Location"] = buff['redirect']
                status_code = 302
            else:

                if 'pageTitle' in data.keys():
                    data['pageTitle'] = data['pageTitle']
                if 'site_url' not in data.keys():
                    data['site_url'] = "//" + settings.ALLOWED_HOSTS[0]

                tmpl = buff['template'] if type(buff) is dict and 'template' in buff.keys() else gen_template_name(
                    method.__name__)
                app_name = method.__globals__['__file__'].split("/")[-2]

                # adding included templates
                for t in tmplIncs:
                    [f, found] = check_for_template(app_name, t, "html")
                    if found:
                        data.update({t: render_to_string(f, data)})

                # generate html repsonse
                [f, found] = check_for_template(app_name, tmpl, "html", True)
                r = render(None, f, data)

        r.status_code = status_code

        if type(buff) is dict:
            if 'headers' in buff.keys():
                r = add_headers(r, buff['headers'])

            if 'cookies' in buff.keys():
                r = add_cookies(r, buff['cookies'])

        return r

    return f


"""
@description        decorator method for sending a json response
"""


def rest(method=None):
    if method is None:
        return functools.partial(rest)

    @functools.wraps(method)
    def f(*args, **kwargs):
        # produce result of method
        res = method(*args, **kwargs)

        [data, status_code, buff] = detect_response_type(res)

        r = gen_response(method, data)
        r.status_code = status_code

        if type(buff) is dict:
            if 'headers' in buff.keys():
                r = add_headers(r, buff['headers'])

            if 'cookies' in buff.keys():
                r = add_cookies(r, buff['cookies'])

        return r

    return f


"""
@description        decorator method for sending a hex response
"""


def binhex(method=None):
    if method is None:
        return functools.partial(binhex)

    @functools.wraps(method)
    def f(*args, **kwargs):
        # produce result of method
        res = method(*args, **kwargs)
        [data, status_code] = detect_bin_response_type(res, method)

        r = HttpResponse(data)
        r.status_code = status_code

        return r

    return f


def detect_bin_response_type(res, method):
    if type(res) is int:
        data = b""
        status_code = res
    elif type(res) is bytes:
        data = res
        status_code = SUCCESSFUL_RESPONSE
    elif type(res) is str:
        data = res.encode()
        status_code = SUCCESSFUL_RESPONSE
    elif type(res) is list and len(res) == 2 and type(res[0]) is int and type(res[1]) is str:
        data = res[1].encode()
        status_code = res[0]
    elif type(res) is tuple and len(res) == 2 and type(res[0]) is int and type(res[1]) is str:
        data = res[1].encode()
        status_code = res[0]
    elif type(res) is list and len(res) == 2 and type(res[0]) is str and type(res[1]) is int:
        data = res[0].encode()
        status_code = res[1]
    elif type(res) is tuple and len(res) == 2 and type(res[0]) is str and type(res[1]) is int:
        data = res[0].encode()
        status_code = res[1]
    elif type(res) is list and len(res) == 2 and type(res[0]) is int and type(res[1]) is bytes:
        data = res[1]
        status_code = res[0]
    elif type(res) is tuple and len(res) == 2 and type(res[0]) is int and type(res[1]) is bytes:
        data = res[1]
        status_code = res[0]
    elif type(res) is list and len(res) == 2 and type(res[0]) is bytes and type(res[1]) is int:
        data = res[0]
        status_code = res[1]
    elif type(res) is tuple and len(res) == 2 and type(res[0]) is bytes and type(res[1]) is int:
        data = res[0]
        status_code = res[1]
    else:
        raise Exception('for using @binhex, result of ' + str(
            method.__name__) + " must be as [str data, int status_code] or [int status_code,"
                               " str data] or a status integer or a str of data")

    return [data, status_code]


def detect_response_type(res):
    if type(res) is int:
        data = {}
        status_code = res
    elif type(res) is dict:
        data = res
        status_code = SUCCESSFUL_RESPONSE
    elif type(res) is list and len(res) == 2 and type(res[0]) is int and (type(res[1]) is dict or type(res[1]) is list):
        data = res[1]
        status_code = res[0]
    elif type(res) is list and len(res) == 2 and type(res[1]) is int and (type(res[0]) is dict or type(res[0]) is list):
        data = res[0]
        status_code = res[1]
    elif type(res) is tuple and len(res) == 2 and type(res[0]) is int and (
            type(res[1]) is dict or type(res[1]) is list):
        data = res[1]
        status_code = res[0]
    elif type(res) is tuple and len(res) == 2 and type(res[0]) is int and type(res[1]) is str:
        data = [res[1]]
        status_code = res[0]
    elif type(res) is tuple and len(res) == 2 and type(res[1]) is int and type(res[0]) is str:
        data = [res[0]]
        status_code = res[1]
    elif type(res) is tuple and len(res) == 2 and type(res[1]) is int and (
            type(res[0]) is dict or type(res[0]) is list):
        data = res[0]
        status_code = res[1]
    elif type(res) is list:
        data = res
        status_code = SUCCESSFUL_RESPONSE
    else:
        try:
            [p1, p2] = res
            if type(p1) is int and (type(p2) is dict or type(p2) is list):
                data = p2
                status_code = p1
            elif type(p2) is int and (type(p1) is dict or type(p1) is list):
                data = p1
                status_code = p2
            else:
                raise ValueError()
        except:
            status_code = 500
            try:
                data = [res.content.decode('utf-8')]
            except:
                data = [res]

    buff = data.copy() if type(data) is dict else []

    for x in ['headers', 'cookies', 'template', 'redirect']:
        try:
            del data[x]
        except:
            pass

    return [data, status_code, buff]


def gen_response(method, data):
    tmpl = data['template'] if type(data) is dict and 'template' in data.keys() else gen_template_name(method.__name__)
    app_name = method.__globals__['__file__'].split(os.path.sep)[-2]
    for t in tmplIncs:
        [f, found] = check_for_template(app_name, t, "api")
        if found:
            data.update({t: render_to_string(f, data)})

    # check for template or don't use template
    [f, found] = check_for_template(app_name, tmpl, "api")
    if found:
        r = HttpResponse(render_to_string(f, data), content_type='application/json')
    else:
        r = JsonResponse(data, safe=False)

    return r


def add_headers(r, headers):
    for n, v in headers.items():
        r.headers[n] = v
    return r


def add_cookies(r, cookies):
    for n, v in cookies.items():
        if type(v) is tuple:
            age = v[1]
            v = v[0]
        else:
            age = 7 * 86400
        r.set_cookie(n, v, max_age=age)
    return r


"""
@description        decorator method for create a piece html code as a response or as a string
@param  resType     @required integer       PIECE_AS_STRING or PIECE_AS_RESPONSE
"""


def piece(resType):
    def p(func):
        @functools.wraps(func)
        def response_Piece(*args, **kwargs):
            # produce result of func
            res = func(*args, **kwargs)
            if type(res) is dict:
                data = res
                status_code = SUCCESSFUL_RESPONSE
            else:
                try:
                    [data, status_code] = res
                except:
                    raise Exception('for using @piece, result of ' + str(
                        func.__name__) + " must be as [dict data, int status_code] or a dict of data")

            tmpl = gen_template_name(func.__name__)
            global AppBaseapp_name
            [f, found] = check_for_template(AppBaseapp_name, tmpl, "piece")

            if resType == PIECE_AS_STRING:
                return render_to_string(f, data)

            if resType == PIECE_AS_RESPONSE:
                r = render(None, f, data)
                r.status_code = status_code

                headers = [] if 'headers' not in kwargs else kwargs['headers']
                for n, v in headers:
                    r[n] = v

                return r
            else:
                raise Exception('for using @piece(resType), resType must be PIECE_AS_STRING or PIECE_AS_RESPONSE')

        return response_Piece

    return p
