import numpy as np

POPULARITY_MIN_MONTH = '2012-01-01'
METRIC_PRECISION = {
    'default': 1,
    'abv': 1,
    'ibu': 1,
    'srm': 1,
    'og': 3,
    'fg': 3,
}


def lowerfence(x):
    return x.quantile(0.02)


def q1(x):
    return x.quantile(0.25)


def q3(x):
    return x.quantile(0.75)


def upperfence(x):
    return x.quantile(0.98)


def slope(d):
    if len(d) < 4:
        return 0
    return np.polyfit(np.linspace(0, 1, len(d)), d, 1)[0]
