from .classes import Error, Errors


def parse_const(const):
    def _parse_const(key, value):
        return const
    return _parse_const


# Similar to parse_const, but fails if a non None value is given
# Useful for setting default with parse_one_of in parse_dict
def parse_default(default):
    def _parse_const(key, value):
        if value is None:
            return default
        else:
            return Error("Not using default [%s]." % default)
    return _parse_const


def parse_int(key, value):
    if isinstance(value, int):
        return value
    else:
        return Error("'%s' should be int, is: '%s'"
                     % (key, type(value).__name__))


def parse_string(key, value):
    if isinstance(value, str):
        return value
    else:
        return Error("'%s' should be string, is: '%s'"
                     % (key, type(value).__name__))


# Parse as homogeneous list, use parse_one_of for heterogeneous lists
# and parse_and_map to regain homogeneity
def parse_list(of):
    def _parse_list(key, value):
        ret = []
        if isinstance(value, list):
            for index, element in enumerate(value):
                parsed = of("%s[%s]" % (key, index), element)
                if isinstance(parsed, Error):
                    return parsed
                ret.append(parsed)
            return ret
        else:
            return Error("'%s' should be list, is: '%s'"
                         % (key, type(value).__name__))
    return _parse_list


# give a dict of keys and their respective parser function
# a missing key is treated as None, but missing key is
# reported on fail
def parse_dict(keys):
    def _parse_dict(key, value):
        parsed = {}
        errors = []
        if isinstance(value, dict):
            for _key, parser in keys.items():
                if _key in value:
                    _value = parser("%s.%s" % (key, _key), value[_key])
                    if isinstance(_value, Error):
                        errors.append(_value)
                else:
                    _value = parser("%s.%s" % (key, _key), None)
                    if isinstance(_value, Error):
                        errors.append(Error("'%s' missing key: '%s'"
                                            % (key, _key)))
                parsed[_key] = _value

        else:
            return Error("'%s' should be dict, is: '%s'"
                         % (key, type(value).__name__))
        if errors:
            return Errors(errors)
        return parsed
    return _parse_dict


def parse_choice(*choices):
    def _parse_choice(key, value):
        if value in choices:
            return value
        else:
            return Error("'%s' should be one of %s, is: '%s'"
                         % (key, choices, value))
    return _parse_choice


# tries out the list of parsers and returns the first
# successful one
def parse_one_of(*parsers):
    def _parse_one_of(key, value):
        errors = []
        for parser in parsers:
            ret = parser(key, value)
            if isinstance(ret, Error):
                errors.append(ret)
            else:
                return ret
        else:
            error = Error("All attempts failed for '%s':")
            return Errors([error] + errors)
    return _parse_one_of


# try the parser and apply function to the value if successful
def parse_and_map(parser, f):
    def _parse_and_map(key, value):
        ret = parser(key, value)
        if isinstance(ret, Error):
            return ret
        return f(ret)
    return _parse_and_map


if __name__ == "__main__":

    def _assert(cond):
        if not cond:
            raise AssertionError()

    def is_error(o):
        return isinstance(o, Error)

    # Test the parsing funtions
    the_error = Error()
    fail = parse_const(the_error)

    # parse_string
    # Contract: return passed value if string, else Error
    _assert(parse_string("", "abc") == "abc")
    _assert(is_error(parse_string("", {})))
    _assert(is_error(parse_string("", 42)))

    # parse_int
    # Contract: return passed value if int, else Error
    _assert(parse_int("", 1) == 1)
    _assert(is_error(parse_int("", {})))
    _assert(is_error(parse_int("", "42")))

    # parse_const
    # Contract: always return const
    _assert(parse_const("abc")("", "abc") == "abc")
    _assert(parse_const(the_error)("", "abc") is the_error)

    # parse_default
    # Contract: return default iff None was given as value
    _assert(parse_default(the_error)("", None) is the_error)
    _assert(not parse_default(the_error)("", "abc") is the_error)
    _assert(is_error(parse_default(the_error)("", "abc")))

    # parse_and_map
    # Contract: apply f on parsed value iff successful, else pass the error
    _assert(parse_and_map(parse_string, str.upper)("", "abc") == "ABC")
    _assert(parse_and_map(parse_int, str)("", 21) == "21")
    _assert(parse_and_map(fail, str.upper)("", "abc") is the_error)

    # parse_one_of
    # Contract: try supplied parsers, return value of successful, else Error
    _assert(parse_one_of(parse_int, parse_string, fail)("", 123) == 123)
    _assert(parse_one_of(parse_int, parse_string, fail)("", "abc") == "abc")
    _assert(is_error(parse_one_of(parse_int, parse_string, fail)("", [123])))
    _assert(is_error(parse_one_of(fail, fail)("", "")))

    # parse_choice
    # Contract: return value if in choices, else Error
    _assert(parse_choice(*"abc")("", "b") == "b")
    _assert(is_error(parse_choice(*"abc")("", "d")))

    # parse_list
    # Contract: apply parser to list, if any fail return the error
    parse_string_and_int = parse_one_of(parse_string,
                                        parse_and_map(parse_int, str))
    _assert(parse_string_and_int("", 21) == "21")
    _assert(parse_string_and_int("", 42) == "42")
    _assert(parse_list(parse_string)("", ["halo", "welt"]) == ["halo", "welt"])
    _assert(parse_list(parse_string_and_int)("", ["21", 42]) == ["21", "42"])
    _assert(is_error(parse_list(parse_string)("", 42)))
    _assert(is_error(parse_list(parse_string)("", ["halo", {}])))

    # parse_dict
    # Contract: apply parser of key to value of key in passed value,
    # if any fail return the errors

    _assert(parse_dict({'x': parse_int})("", {'x': 42}) == {'x': 42})
    _assert(is_error(parse_dict({'x': parse_string})("", {'x': 42})))
    _assert(is_error(parse_dict({'x': parse_string})("", {})))
