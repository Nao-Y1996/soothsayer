import regex


def extract_enclosed(text: str) -> list[str]:
    """
    Extract substrings enclosed within `<<` and `>>` with support for nested patterns.

    Parameters
    ----------
    text : str
        The input string in which to search for enclosed substrings.

    Returns
    -------
    list of str
        A list containing all substrings found between `<<` and `>>`. Supports nested patterns recursively.

    Examples
    --------
    >>> extract_enclosed("This is <<an example>> string.")
    ['an example']
    >>> extract_enclosed("<<Nested <<inner>> example>>")
    ['Nested <<inner>> example']
    """
    pattern = r"<<((?:[^<>]+|(?R))*)>>"
    return regex.findall(pattern, text)


def remove_enclosed(text: str) -> str:
    """
    Remove substrings enclosed within `<<` and `>>`, including the delimiters, from the input text.

    Parameters
    ----------
    text : str
        The input string from which enclosed substrings and their delimiters will be removed.

    Returns
    -------
    str
        The resulting string after removing all substrings enclosed by `<<` and `>>`.

    Examples
    --------
    >>> remove_enclosed("This is <<an example>> string.")
    'This is  string.'
    >>> remove_enclosed("Before <<nested <<inner>> example>> after")
    'Before  after'
    """
    pattern = r"<<((?:[^<>]+|(?R))*)>>"
    return regex.sub(pattern, "", text)
