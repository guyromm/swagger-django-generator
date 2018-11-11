"""
Do not modify this file. It is generated from the Swagger specification.

If you need to tweak the functionality in this file, you can replace it
with your own.
"""
from functools import wraps
import base64
import json
import jsonschema
import logging
import sys
import uuid
import datetime
import jwt

from django.contrib.auth import user_logged_in, authenticate, login, get_user_model
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.conf import settings


_LOGGER = logging.getLogger(__name__)


class AuthenticationFailed(SuspiciousOperation):
    pass


def body_to_dict(body, schema):
    # type: (str, Dict) -> Dict
    """

    :param body: The body content
    :param schema: The expected JSONSchema
    :return: A dictionary containing the parsed body
    :raises SuspiciousOperation: If the body is not in JSON format, or does not
       conform to the specified schema.
    """
    try:
        data = json.loads(body.decode('utf-8'))
        jsonschema.validate(data, schema=schema)
        return data
    except Exception as e:
        # The SuspiciousOperation exception will result in an
        # HttpResponseBadRequest response.
        raise SuspiciousOperation(e)


def get_secure_key(user_id):
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    salt = getattr(
        settings,
        'JWT_SALT',
        getattr(settings, 'SECRET_KEY'))
    key = user.password + salt
    return key, user


def obtain_jwt(attrs, algorithm='HS256'):
    """
    """
    delta = getattr(
        settings,
        'JWT_EXPIRATION',
        datetime.timedelta(seconds=300),
    )
    username_field = get_user_model().USERNAME_FIELD
    credentials = {
        username_field: attrs.get(username_field),
        'password': attrs.get('password')
    }
    user = authenticate(
        **credentials
    )
    payload = {
        'user_id': user.pk,
        'exp': datetime.datetime.utcnow() + delta
    }
    key, user = get_secure_key(user.pk)
    token = jwt.encode(
        payload,
        key,
        algorithm,
    ).decode('utf-8')
    user_logged_in.send(sender=user.__class__, user=user)
    return {
        'token': token
    }


def authenticate_jwt(request, algorithm='HS256'):
    auth = request.META["HTTP_AUTHORIZATION"].split()
    if 'jwt' != auth[0].lower():
        raise AuthenticationFailed('Invalid token')

    try:
        token = auth[1]
        unverified_payload = jwt.decode(
            jwt=token,
            key=None,
            verify=False,
            algorithms=[algorithm],
        )
        user_id = unverified_payload.get('user_id')
        key, user = get_secure_key(user_id)
        if not user or not user.is_active:
            raise AuthenticationFailed('Invalid token')

        payload = jwt.decode(
            jwt=token,
            key=key,
            verify=True,
            algorithms=[algorithm],
        )
        request.user = user
        return user
    except jwt.ExpiredSignature:
        raise AuthenticationFailed('The signature has expired')

    except jwt.DecodeError:
        raise AuthenticationFailed('Error decoding the signature')

    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Invalid token')


def login_required_no_redirect(view_func):
    """
    Helper function that returns an HTTP 401 response if the user making the
    request is not logged in, or did not provide basic HTTP authentication in
    the request.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        {% for sec_desc, sec_type in security_defs|dictsort(true) %}
        {% if sec_desc == 'basic' %}
        if "HTTP_AUTHORIZATION" in request.META:
            auth = request.META["HTTP_AUTHORIZATION"].split()
            if len(auth) == 2:
                # NOTE: We only support basic authentication for now.
                if auth[0].lower() == "basic":
                    base_val = base64.b64decode(auth[1])
                    if sys.version_info[0] > 2:
                        base_val = base_val.decode()
                    uname, passwd = base_val.split(":")
                    user = authenticate(username=uname, password=passwd)
                    if user and user.is_active:
                        login(request, user)
                        request.user = user
                        return view_func(request, *args, **kwargs)
        {% elif sec_desc == "apiKey" and sec_type["desc"] == "JWT" %}
        if authenticate_jwt(request):
            return view_func(request, *args, **kwargs)
        {% elif sec_desc == "apiKey" and sec_type["desc"] != "JWT" %}
        if "HTTP_X_API_KEY" in request.META:
            key = request.META["HTTP_X_API_KEY"]
            # shared keys for development, must be defined in settings.py
            if key in settings.ALLOWED_API_KEYS:
                User = get_user_model()
                user = User.objects.get(username=settings.ALLOWED_API_KEYS[key])
                login(request,user)
                request.user = user
                return view_func(request, *args, **kwargs)
        {% endif %}
        {% endfor %}
        return HttpResponse("Unauthorized", status=401)

    return wrapper


@jsonschema.FormatChecker.cls_checks("uuid")
def check_uuid_format(instance):
    try:
        uuid.UUID(instance)
        return True
    except ValueError:
        return False


# The instance of the format checker must be created after
# the UUID format checker was registered.
_FORMAT_CHECKER = jsonschema.FormatChecker()

# Be explicit about which formats are supported. More information can be found here:
# http://python-jsonschema.readthedocs.io/en/stable/validate/#jsonschema.FormatChecker
_LOGGER.info("The following formats will be validated: {}".format(
             ", ".join(_FORMAT_CHECKER.checkers.keys())))


def validate(instance, schema):
    jsonschema.validate(instance, schema=schema,
                        format_checker=_FORMAT_CHECKER)
