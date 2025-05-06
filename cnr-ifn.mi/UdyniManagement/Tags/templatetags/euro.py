from django import template
import re

register = template.Library()


@register.filter
def euro(value):

    s_val = "{0:.2f}".format(value)
    while True:
        s_new = re.sub(r"^(-?\d+)(\d{3})", r"\g<1>'\g<2>", s_val)
        if s_new != s_val:
            s_val = s_new
        else:
            break

    return "€ {0:s}".format(re.sub(r"\.", r",", s_new))
