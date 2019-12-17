import re
from fnmatch import fnmatch


__all__ = ['make_matcher']


def make_matcher(name, value, use_regex):
    """
    This function returns a function that is responsible for determining a
    string-pattern-match.  This program supports two different types of
    pattern matching.  By default it uses "glob" matching.  If the User
    specifies the -R/--use-regex option, then this program will use regex
    matching.

    Parameters
    ----------
    name : str - parameter name, e.g. "hostname"
    value : str - the Command parameter value, e.g. "tr*"
    use_regex : bool - True if match using regex, False use glob

    Returns
    -------
    function(str)->bool.
    """
    import sre_constants

    if use_regex:
        try:
            _re_host = re.compile(value, re.IGNORECASE)

        except sre_constants.error:
            raise ValueError(
                f'Bad regular expression for option {name}: {value}',
            )

        def regex_matcher(_in_val):
            return bool(_re_host.match(_in_val))

        return regex_matcher

    def fnmatch_matcher(_in_val):
        return fnmatch(_in_val, value)

    return fnmatch_matcher
