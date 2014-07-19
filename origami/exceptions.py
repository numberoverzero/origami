class OrigamiException(Exception):
    pass


class InvalidPatternClassException(OrigamiException):
    def __init__(self, cls, reason):
        message = "Invalid pattern class '{}': ".format(cls) + reason
        OrigamiException.__init__(self, message)


class InvalidFoldFormatException(OrigamiException):
    def __init__(self, fold, reason):
        message = "Invalid fold '{}': ".format(fold) + reason
        OrigamiException.__init__(self, message)


class InvalidCreaseFormatException(OrigamiException):
    def __init__(self, crease, reason):
        message = "Invalid crease '{}': ".format(crease) + reason
        OrigamiException.__init__(self, message)


class FoldingException(OrigamiException):
    def __init__(self, obj, reason):
        message = "Failed to fold '{}': ".format(obj) + reason
        OrigamiException.__init__(self, message)


class UnfoldingException(OrigamiException):
    def __init__(self, obj, reason):
        message = "Failed to unfold '{}': ".format(obj) + reason
        OrigamiException.__init__(self, message)
