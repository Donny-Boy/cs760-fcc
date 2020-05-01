#!/usr/bin/python3
#
# Author: Steve Landherr <landherr@cs.wisc.edu>
#
# Module containing functions to extract and standardize feature values
# from source datasets.
import dateutil.parser

exception_values = {'NULL', 'OVER', 'EMPTY', 'MISSING', 'INVALID'}


def date(value):
    if value is None:
        raise ValueError('NULL')
    if not isinstance(value, str):
        raise ValueError('INVALID')
    try:
        return dateutil.parser.isoparse(value).timestamp()
    except ValueError:
        raise ValueError('INVALID')


def integer(value):
    if value is None:
        raise ValueError('NULL')
    try:
        return int(value)
    except ValueError:
        raise ValueError('INVALID')


def floating_point(value):
    if value is None:
        raise ValueError('NULL')
    try:
        return float(value)
    except ValueError:
        raise ValueError('INVALID')


def boolean(value):
    """
    booleans standardize to one of three values:
     1.0: True
     -1.0: False
     0.0: Unknown

    :param value: boolean value to standardize (str / bool / float)
    :return: standardized value (float)
    """
    if value is None:
        return 0.0
    try:
        value = floating_point(value)
    except ValueError:
        pass
    if isinstance(value, float):
        if value != 0.0:
            return 1.0
        else:
            return -1.0
    if isinstance(value, bool):
        if value:
            return 1.0
        else:
            return -1.0
    if isinstance(value, str):
        if not value:
            return 0.0
        if value in ['True', 'true']:
            return 1.0
        if value in ['False', 'false']:
            return -1.0
    return 0.0


def city_state(value):
    if value is None:
        raise ValueError('NULL')
    if not isinstance(value, str):
        raise ValueError('INVALID')

    # disallow special characters
    forbidden_characters = set('%{}|$&^;<>?@!#*+=\\[]')
    # map underscores and periods to spaces, and remove commas
    mapped_characters = str.maketrans('_.', '  ', ',')

    if not set(value).isdisjoint(forbidden_characters):
        raise ValueError('INVALID')
    value = string(value.translate(mapped_characters))
    return value


def md5hash(value):
    value = string(value)
    if len(value) != 32:
        raise ValueError('INVALID')
    return value


def string(value):
    """
    Standardize the string to lowercase with extraneous spaces removed.
    (10 words max to filter out noisy raw data.)

    :param value: element value to standardize (str)
    :return: standardized value (str)
    """
    if value is None:
        raise ValueError('NULL')
    if not isinstance(value, str):
        raise ValueError('INVALID')
    words = value.lower().split()
    if len(words) >= 10:
        raise ValueError('OVER')
    if len(words) == 0:
        raise ValueError('EMPTY')
    return ' '.join(words)


def element(element_spec, source):
    """
    Extract standardized value of element from source dataset.

    Supports concatenating multiple elements, as well as alternate locations
    for elements in the source.

    :param source: raw source data (dict)
    :param element_spec: source element to extract and standardize (dict)
    :return: the standardized value of the extracted element
    """
    standard_value = None
    for option in element_spec['definition']:
        values = list()
        try:
            for component in option:
                found = source
                for item in component:
                    found = found[item]
                if 'filter' in element_spec:
                    found = element_spec['filter'](found)
                values.append(found)
        except KeyError:
            values = ['MISSING']
        except ValueError as exc:
            if str(exc) not in exception_values:
                raise exc
            values = [str(exc)]
        last_value = standard_value
        if len(values) > 1:
            standard_value = ' '.join(values)
        else:
            standard_value = values[0]
        # Use the first non-exception value
        if standard_value not in exception_values:
            break
        # Otherwise keep processing, but keep the first exception value
        # in case all options are exceptions.
        if last_value is not None:
            standard_value = last_value
    return standard_value
