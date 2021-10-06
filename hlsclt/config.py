from .classes import Error, Errors
from types import SimpleNamespace


def decode_const(const):
    def _decode_const(key, value):
        return const
    return _decode_const


# Similar to decode_const, but fails if a non None value is given
# Useful for setting default with decode_one_of in decode_obj
def decode_default(default):
    def _decode_const(key, value):
        if value is None:
            return default
        else:
            return Error("Not using default [%s]." % default)
    return _decode_const


def decode_int(key, value):
    if isinstance(value, int):
        return value
    else:
        return Error("'%s' should be int, is: '%s'"
                     % (key, type(value).__name__))


def decode_string(key, value):
    if type(value) is str:
        return value
    else:
        return Error("'%s' should be string, is: '%s'"
                     % (key, type(value).__name__))


# Parse as homogeneous list, use decode_one_of for heterogeneous lists
# and decode_and_map to regain homogeneity
def decode_list(of):
    def _decode_list(key, value):
        ret = []
        if isinstance(value, list):
            for index, element in enumerate(value):
                decoded = of("%s[%s]" % (key, index), element)
                if isinstance(decoded, Error):
                    return decoded
                ret.append(decoded)
            return ret
        else:
            return Error("'%s' should be list, is: '%s'"
                         % (key, type(value).__name__))
    return _decode_list


# give a dict of keys and their respective decoding function
# a missing key is treated as None, but missing key is
# reported on fail
def decode_obj(keys):
    def _decode_obj(key, value):
        decoded = {}
        errors = []
        if isinstance(value, dict):
            for _key, decoder in keys.items():
                if _key in value:
                    _value = decoder("%s.%s" % (key, _key), value[_key])
                    if isinstance(_value, Error):
                        errors.append(_value)
                else:
                    _value = decoder("%s.%s" % (key, _key), None)
                    if isinstance(_value, Error):
                        errors.append(Error("'%s' missing key: '%s'"
                                            % (key, _key)))
                decoded[_key] = _value

        else:
            return Error("'%s' should be dict, is: '%s'"
                         % (key, type(value).__name__))
        if errors:
            return Errors(errors)
        return SimpleNamespace(**decoded)
    return _decode_obj


def decode_choice(*choices):
    def _decode_choice(key, value):
        if value in choices:
            return value
        else:
            return Error("'%s' should be one of %s, is: '%s'"
                         % (key, choices, value))
    return _decode_choice


# tries out the list of decoders and returns the first
# successful one
def decode_one_of(*decoders):
    def _decode_one_of(key, value):
        errors = []
        for decoder in decoders:
            ret = decoder(key, value)
            if isinstance(ret, Error):
                errors.append(ret)
            else:
                return ret
        else:
            error = Error("All attempts failed for '%s':")
            return Errors([error] + errors)
    return _decode_one_of


# try the decoder and apply function to the value if successful
def decode_and_map(decoder, f):
    def _decode_and_map(key, value):
        ret = decoder(key, value)
        if isinstance(ret, Error):
            return ret
        return f(ret)
    return _decode_and_map


if __name__ == "__main__":

    def _assert(cond):
        if not cond:
            raise AssertionError()

    def is_error(o):
        return isinstance(o, Error)

    # Test the parsing funtions
    the_error = Error()
    fail = decode_const(the_error)

    # decode_string
    # Contract: return passed value if string, else Error
    _assert(decode_string("", "abc") == "abc")
    _assert(is_error(decode_string("", {})))
    _assert(is_error(decode_string("", 42)))

    # decode_int
    # Contract: return passed value if int, else Error
    _assert(decode_int("", 1) == 1)
    _assert(is_error(decode_int("", {})))
    _assert(is_error(decode_int("", "42")))

    # decode_const
    # Contract: always return const
    _assert(decode_const("abc")("", "abc") == "abc")
    _assert(decode_const(the_error)("", "abc") is the_error)

    # decode_default
    # Contract: return default iff None was given as value
    _assert(decode_default(the_error)("", None) is the_error)
    _assert(not decode_default(the_error)("", "abc") is the_error)
    _assert(is_error(decode_default(the_error)("", "abc")))

    # decode_and_map
    # Contract: apply f on decoded value iff successful, else pass the error
    _assert(decode_and_map(decode_string, str.upper)("", "abc") == "ABC")
    _assert(decode_and_map(decode_int, str)("", 21) == "21")
    _assert(decode_and_map(fail, str.upper)("", "abc") is the_error)

    # decode_one_of
    # Contract: try supplied decoders, return value of successful, else Error
    _assert(decode_one_of(decode_int, decode_string, fail)("", 123) == 123)
    _assert(decode_one_of(decode_int, decode_string, fail)("", "abc") == "abc")
    _assert(is_error(decode_one_of(decode_int, decode_string, fail)("", [123])))
    _assert(is_error(decode_one_of(fail, fail)("", "")))

    # decode_choice
    # Contract: return value if in choices, else Error
    _assert(decode_choice(*"abc")("", "b") == "b")
    _assert(is_error(decode_choice(*"abc")("", "d")))

    # decode_list
    # Contract: apply decoder to list, if any fail return the error
    decode_string_and_int = decode_one_of(decode_string,
                                          decode_and_map(decode_int, str))
    _assert(decode_string_and_int("", 21) == "21")
    _assert(decode_string_and_int("", 42) == "42")
    _assert(decode_list(decode_string)("", ["halo", "welt"]) == ["halo", "welt"])
    _assert(decode_list(decode_string_and_int)("", ["21", 42]) == ["21", "42"])
    _assert(is_error(decode_list(decode_string)("", 42)))
    _assert(is_error(decode_list(decode_string)("", ["halo", {}])))

    # decode_obj
    # Contract: apply decoder of key to value of key in passed value,
    # if any fail return the errors

    _assert(vars(decode_obj({'x': decode_int})("", {'x': 42})) == {'x': 42})
    _assert(is_error(decode_obj({'x': decode_string})("", {'x': 42})))
    _assert(is_error(decode_obj({'x': decode_string})("", {})))
