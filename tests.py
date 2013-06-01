from origami import Crafter, pattern, fold, unfold
from bitstring import CreationError
import unittest
import uuid


def init(*attrs):
    def fn(self, *args):
        for attr, arg in zip(attrs, args):
            setattr(self, attr, arg)
    return fn


def equals(*attrs):
    def eq(self, other):
        try:
            eq_ = lambda at: getattr(self, at) == getattr(other, at)
            return all(map(eq_, attrs))
        except AttributeError:
            return False
    return eq


def unique_crafter():
    return str(uuid.uuid4())


class GlobalFolderTests(unittest.TestCase):
    '''Unit tests for the @pattern decorator (using global crafter)'''

    def setUp(self):
        @pattern()
        class Blob(object):
            origami_folds = 'n=uint:8'
            clsatr = "Some Value"
            init_calls = 0

            def __init__(self, n='empty'):
                self.n = n
                Blob.init_calls += 1

            __eq__ = equals('n')

        self.Blob = Blob

    def tearDown(self):
        # Dump learned patterns or we'll hit key errors when we recreate Blob in setUp
        Crafter('global').patterns = {}

    def testClassAttributesUnchanged(self):
        '''@pattern decorator shouldn't modify existing class attributes'''
        blob = self.Blob('full')

        assert blob.n == 'full'
        assert blob.clsatr == "Some Value"
        assert self.Blob.clsatr == "Some Value"

    def testCannotRegisterSameClassName(self):
        with self.assertRaises(KeyError):
            @pattern()
            class Blob(object):
                origami_folds = 'o=uint:9'

    def testUnfoldMethodUsesDefaultInit(self):
        '''
        When None is passed to the unfold method on the class, the default constructor should be called.
        '''
        data = {'n': 'full'}
        blob = self.Blob.unfold('global', None, **data)

        assert blob.n == 'full'
        assert self.Blob.init_calls > 0

    def testUnfoldMethodUsesInstance(self):
        '''
        When an instance of the class is passed to unfold, it should not call the constructor.
        '''
        data = {'n': 'full'}
        blob = self.Blob('empty')
        blob = self.Blob.unfold('global', blob, **data)

        assert blob.n == 'full'
        assert self.Blob.init_calls == 1

    def testUnfoldExtraKwargs(self):
        '''
        Passing extra kwargs to the unfold method on the class should be ok.
        '''
        data = {'n': 'full', 'junk': 'unused'}
        blob = self.Blob.unfold('global', None, **data)

        assert blob.n == 'full'
        assert not hasattr(blob, 'junk')

    def testUnfoldMissingKwargs(self):
        '''
        Passing too few kwargs to the unfold method on the class should raise an AttributeError.
        '''
        data = {'junk': 'unused'}
        try_unfold = lambda: self.Blob.unfold('global', None, **data)

        self.assertRaises(AttributeError, try_unfold)


class TranslatorTests(unittest.TestCase):
    '''Unit tests for attribute and format creases'''

    def setUp(self):
        self.n = unique_crafter()
        self.c = Crafter(self.n)

    def testNoTranslators(self):
        '''No origami_creases attribute defined'''

        @pattern(self.n)
        class Blob(object):
            origami_folds = 'enabled=uint:1, alpha=uint:8'

            __eq__ = equals('enabled', 'alpha')

        blob = Blob()
        blob.enabled = 1
        blob.alpha = 127

        data = self.c.fold(blob)
        other_blob = self.c.unfold(Blob, data)
        assert blob == other_blob

    def testTranslatorsIsNone(self):
        '''origami_creases attribute is None'''

        @pattern(self.n)
        class Blob(object):
            origami_folds = 'enabled=uint:1, alpha=uint:8'
            origami_creases = None

            __eq__ = equals('enabled', 'alpha')

        blob = Blob()
        blob.enabled = 1
        blob.alpha = 127

        data = self.c.fold(blob)
        other_blob = self.c.unfold(Blob, data)
        assert blob == other_blob

    def testTranslatorsIsEmpty(self):
        '''origami_creases attribute is {}'''

        @pattern(self.n)
        class Blob(object):
            origami_folds = 'enabled=uint:1, alpha=uint:8'
            origami_creases = {}

            __eq__ = equals('enabled', 'alpha')

        blob = Blob()
        blob.enabled = 1
        blob.alpha = 127

        data = self.c.fold(blob)
        other_blob = self.c.unfold(Blob, data)
        assert blob == other_blob

    def testSingleNamedTranslator(self):
        '''Named creases should work on specified fields'''

        @pattern(self.n)
        class Blob(object):
            origami_folds = 'enabled=uint:1, r=uint:8, g=uint:8, b=uint:8'
            origami_creases = {'enabled': {'fold': int, 'unfold': bool}}

            __eq__ = equals('enabled', 'r', 'g', 'b')

        blob = Blob()
        blob.enabled = True
        blob.r = 127
        blob.g = 128
        blob.b = 129

        data = self.c.fold(blob)
        other_blob = self.c.unfold(Blob, data)

        assert blob == other_blob

    def testSingleFormatTranslator(self):
        '''Format creases should work on all fields with matching formats'''

        @pattern(self.n)
        class Blob(object):
            origami_folds = 'enabled=uint:1, r=uint:8, g=uint:8, b=uint:8'
            origami_creases = {'uint:8': {'fold': int, 'unfold': str}}

            __eq__ = equals('enabled', 'r', 'g', 'b')

        blob = Blob()
        blob.enabled = 1
        blob.r = '127'
        blob.g = '128'
        blob.b = '129'

        data = self.c.fold(blob)
        other_blob = self.c.unfold(Blob, data)

        assert blob == other_blob

    def testNamedTranslatorsTakePrecedence(self):
        '''When a value is covered by both types of creases, only the name creases should be used.'''

        def never_call(arg):
            assert False

        @pattern(self.n)
        class Blob(object):
            origami_folds = 'enabled=uint:1'
            origami_creases = {
                'enabled': {'fold': int, 'unfold': bool},
                'uint:1': {'fold': never_call, 'unfold': never_call}
            }

            __eq__ = equals('enabled')

        blob = Blob()
        blob.enabled = True

        data = self.c.fold(blob)
        other_blob = self.c.unfold(Blob, data)

        assert blob == other_blob


class NestingTests(unittest.TestCase):
    '''Unit tests for nested folding'''

    def setUp(self):
        self.n = unique_crafter()

    def testSingleNesting(self):

        @pattern(self.n)
        class Address(object):
            origami_folds = 'house_number=uint:7'

            __eq__ = equals('house_number')

        @pattern(self.n)
        class Person(object):
            origami_folds = 'age=uint:10, address=Address, alive=uint:1'

            __eq__ = equals('age', 'address', 'alive')

        address = Address()
        address.house_number = 16
        person = Person()
        person.age = 5
        person.alive = 1
        person.address = address

        data = fold(person)
        other_person = unfold(Person, data, self.n)

        assert person == other_person

    def testInvalidFolds(self):

        # Unknown format
        with self.assertRaises(ValueError):
            @pattern(self.n)
            class Foo1(object):
                origami_folds = 'bar=BADFORMAT'

        # Invalid length specification
        with self.assertRaises(ValueError):
            @pattern(self.n)
            class Foo2(object):
                origami_folds = 'bar=uint:NAN'

        # Missing required length
        with self.assertRaises(ValueError):
            @pattern(self.n)
            class Foo3(object):
                origami_folds = 'bar=uint'

        # Passed length when none is required
        with self.assertRaises(ValueError):
            @pattern(self.n)
            class Foo4(object):
                origami_folds = 'bar=bool:10'


class UnfoldTests(unittest.TestCase):
    '''Unit tests for basic unfolding'''

    def setUp(self):
        self.n = unique_crafter()
        self.c = Crafter(self.n)

        @pattern(self.n, unfold=False)
        class Blob(object):
            origami_folds = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'
            __init__ = init(*list('abcd'))
            __eq__ = equals(*list('abcd'))

            @classmethod
            def unfold(cls, crafter_name, instance, **kwargs):
                instance = instance or cls()
                for attr, value in kwargs.items():
                    setattr(instance, attr, value)
                return instance

        self.Blob = Blob

    def testOjbectUnfolding(self):
        '''Unfold into an object that already exists, not using the class's __init__ function'''

        blob = self.Blob(1, 3, 7, 15)
        other_blob = self.Blob()
        folded_blob = self.c.fold(blob)

        self.c.unfold(other_blob, folded_blob)
        assert blob == other_blob

    def testClassUnfolding(self):
        '''Unfold against a class, using the class's __init__ function'''

        blob = self.Blob(1, 3, 7, 15)
        folded_blob = self.c.fold(blob)

        other_blob = self.c.unfold(self.Blob, folded_blob)
        assert blob == other_blob

    def testClassFoldAttribute(self):
        '''fold and unfold should work with the class's fold_metadata attribute'''

        blob = self.Blob(1, 3, 7, 15)
        s = fold(blob)

        other_blob = unfold(self.Blob, s, self.n)

        some_other_blob = self.Blob('wat', 'oh', 'god', 'no')
        unfold(some_other_blob, s, self.n)

        assert blob == other_blob
        assert blob == some_other_blob


class FoldingTests(unittest.TestCase):
    '''Unit tests for basic folding validation and errors'''

    def setUp(self):

        @pattern(unique_crafter())
        class Blob(object):
            origami_folds = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'
            __init__ = init(*list('abcd'))

        self.Blob = Blob

    def testFoldedLength(self):
        '''
        The length of the folded data in bits should be the sum
        of the bit-widths of its class's origami_folds field
        '''
        blob = self.Blob(1, 3, 7, 15)
        s = fold(blob)

        blob2 = self.Blob(0, 0, 0, 0)
        s2 = fold(blob2)

        assert len(s) == sum(range(5))
        assert len(s2) == sum(range(5))

    def testFoldValueOverflow(self):
        '''When passing a value larger than the defined bit-width can contain, a CreationError should be thrown.'''

        blob = self.Blob(2**8, 1, 1, 1)
        try_fold = lambda: fold(blob)
        self.assertRaises(CreationError, try_fold)

    def testFoldMissingAttribute(self):
        '''
        When an object to be folded is missing attributes named in
        it's class's origami_folds string, an AttributeError is thrown.
        '''

        blob = self.Blob(0)
        try_fold = lambda: fold(blob)

        self.assertRaises(AttributeError, try_fold)
