import re


def multidelim_generator(string, item_delim, subitem_delim, strip=True):
    '''
    Yields the item pairs in a string of items.
    Example:
        string = '1:2-3:4-hello:goodbye'
        item_delim = '-'
        subitem_delim = ':'
        this will yield the following:
            ('1', '2')
            ('3', '4')
            ('hello', 'goodbye')
        if strip is True, strips each of
            the subitems of leading/trailing whitespace
    '''
    for item in string.split(item_delim):
        left, right = item.split(subitem_delim, 1)
        yield left.strip(), right.strip()


_req = [
    'int', 'uint', 'intbe', 'uintbe', 'intle', 'uintle', 'intne',
    'uintne', 'float', 'floatbe', 'floatle', 'floatne'
]
_opt = ['hex', 'oct', 'bin', 'bits']
_none = ['bool', 'ue', 'se', 'uie', 'sie']


def validate_bitstring_format(format):
    match = re.search('^(?P<name>\w+):\d+$', format)
    if match:
        name = match.group('name')
        return name in _req or name in _opt
    match = re.search('^(?P<name>\w+)$', format)
    if match:
        name = match.group('name')
        return name in _none or name in _opt
    return False
