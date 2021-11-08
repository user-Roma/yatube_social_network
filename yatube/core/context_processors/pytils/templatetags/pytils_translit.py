# -*- coding: utf-8 -*-
# -*- test-case-name: pytils.test.templatetags.test_translit -*-
"""
pytils.translit templatetags for Django web-framework
"""

from django import template, conf
from core.context_processors.pytils import translit
from core.context_processors.pytils.templatetags import init_defaults

try:
    # Django 1.4+
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode
    smart_text = smart_unicode

register = template.Library()
debug = conf.settings.DEBUG
encoding = conf.settings.DEFAULT_CHARSET
show_value = getattr(conf.settings, 'PYTILS_SHOW_VALUES_ON_ERROR', False)

default_value, default_uvalue = init_defaults(debug, show_value)

# -- filters --


def translify(text):
    """Translify russian text"""
    try:
        res = translit.translify(smart_text(text, encoding))
    except Exception as err:
        # because filter must die silently
        res = default_value % {'error': err, 'value': text}
    return res


def detranslify(text):
    """Detranslify russian text"""
    try:
        res = translit.detranslify(text)
    except Exception as err:
        # because filter must die silently
        res = default_value % {'error': err, 'value': text}
    return res


def slugify(text):
    """Make slug from (russian) text"""
    try:
        res = translit.slugify(smart_text(text, encoding))
    except Exception as err:
        # because filter must die silently
        res = default_value % {'error': err, 'value': text}
    return res


# -- register filters
register.filter('translify', translify)
register.filter('detranslify', detranslify)
register.filter('slugify', slugify)
