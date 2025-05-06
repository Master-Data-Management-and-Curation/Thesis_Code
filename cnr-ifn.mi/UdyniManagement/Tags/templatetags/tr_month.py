from django import template

register = template.Library()

__months_it = ['gennaio',
               'febbraio',
               'marzo',
               'aprile',
               'maggio',
               'giugno',
               'luglio',
               'agosto',
               'settembre',
               'ottobre',
               'novembre',
               'dicembre']

__months_en = ['January',
               'February',
               'March',
               'April',
               'May',
               'June',
               'July',
               'August',
               'September',
               'October',
               'November',
               'December']


@register.filter
def month_it2en(value):
    try:
        return __months_en[__months_it.index(value)]
    except ValueError:
        return "N.A."


@register.filter
def month_en2it(value):
    try:
        return __months_it[__months_en.index(value)]
    except ValueError:
        return "N.A."


@register.filter
def month_it2num(value):
    try:
        return __months_it.index(value) + 1
    except ValueError:
        return -1


@register.filter
def month_num2it(value):
    try:
        value = int(value)
        if value > 0:
            return __months_it[value - 1]
        raise IndexError
    except Exception:
        return "N.A."


@register.filter
def month_en2num(value):
    try:
        return __months_en.index(value) + 1
    except ValueError:
        return -1


@register.filter
def month_num2en(value):
    try:
        value = int(value)
        if value > 0:
            return __months_en[value - 1]
        raise IndexError
    except Exception:
        return "N.A."
