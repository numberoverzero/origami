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
