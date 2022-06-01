import re, os
from django.conf import settings


def genProfilePicPath(i, f):
    ext = f.split('.')[-1]
    return 'profile/{0}.{1}'.format(i.id, ext)


def gen_template_name(method_name):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', method_name)
    parts = [m.group(0) for m in matches]
    return '_'.join(parts).lower()


def check_for_template(app, tmpl, _type, strict=False):
    if _type == "html":
        f = app + '/html/' + tmpl + '.html'
        f2 = 'html/' + tmpl + '.html'
    elif _type == "api":
        f = app + '/api/' + tmpl + '.json'
        f2 = 'api/' + tmpl + '.json'
    elif _type == "piece":
        f = app + '/piece/' + tmpl + '.html'
        f2 = 'piece/' + tmpl + '.html'
    else:
        raise Exception("we have not template type " + _type)

    f_uri = os.path.join(settings.BASE_DIR, 'Theme', f)
    f2_uri = os.path.join(settings.BASE_DIR, 'Theme', f2)
    found = False

    if os.path.exists(f_uri):
        found = True
    elif os.path.exists(f2_uri):
        f = f2
        found = True

    if not found:
        if strict:
            raise Exception("template " + f_uri + " or " + f2_uri + " not found")
        return [False, False]

    return [f, True]


def check_for_include(f):
    return os.path.exists(os.path.join(settings.BASE_DIR, 'Serve', f))
