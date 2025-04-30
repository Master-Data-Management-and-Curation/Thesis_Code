from django import template

register = template.Library()


@register.filter
def dictkey(d, key):
    try:
        return d[key]
    except KeyError:
        return None
    except Exception as e:
        print("ERROR: {0!s} (d: {1!s}, type(d): {2!s}, key: {3!s}".format(e, d, type(d), key))
        return None


_weekday = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}


@register.filter
def dayofweek(date):
    try:
        return _weekday[date.isoweekday()]
    except Exception:
        return ""

@register.filter
def ordinal(number):
    n = round(number)
    if n == 0:
        return ''
    if n in [11, 12, 13]:
        return 'th'
    s = str(n)
    if s[-1] == '1':
        return 'st'
    elif s[-1] == '2':
        return 'nd'
    elif s[-1] == '3':
        return 'rd'
    else:
        return 'th'

@register.filter
def listindex(l, i):
    return l[i]
