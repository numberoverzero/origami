from origami import Crafter, pattern, fold, unfold
from origami.exceptions import (
    InvalidPatternClassException,
    InvalidFoldFormatException,
    FoldingException,
    UnfoldingException
)

import collections
import bitstring
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


def count_creases(fold, unfold):
    counter = collections.defaultdict(int)

    def fold_(value):
        counter['fold'] += 1
        return fold(value)

    def unfold_(value):
        counter['unfold'] += 1
        return unfold(value)
    return counter, {'fold': fold_, 'unfold': unfold_}


unique_id = lambda: str(uuid.uuid4())


class CrafterTests(unittest.TestCase):
    def setUp(self):
        self.id = unique_id()
        self.crafter = Crafter(self.id)

    def testGlobalCrafter(self):
        assert Crafter().name == 'global'
        assert Crafter() is Crafter('global')

    def testLearnPattern(self):
        class Foo(object):
            pass
        cls = Foo
        unfold_func = lambda: None
        folds = 'a=uint:8'
        creases = {}

        self.crafter.learn_pattern(cls, unfold_func, folds, creases)
        assert cls in self.crafter.patterns

    def testLearnPatternEmptyClass(self):
        cls = None
        unfold_func = lambda: None
        folds = 'a=uint:8'
        creases = {}

        with self.assertRaises(InvalidPatternClassException):
            self.crafter.learn_pattern(cls, unfold_func, folds, creases)

    def testLearnSamePatternTwice(self):
        class Foo(object):
            pass
        cls = Foo
        unfold_func = lambda: None
        folds = 'a=uint:8'
        creases = {}

        self.crafter.learn_pattern(cls, unfold_func, folds, creases)
        with self.assertRaises(InvalidPatternClassException):
            self.crafter.learn_pattern(cls, unfold_func, folds, creases)

    def testLearnPatternInvalidFolds(self):
        class Foo(object):
            pass
        cls = Foo
        unfold_func = lambda: None
        folds = 'a=uint:NotANumber'
        creases = {}

        with self.assertRaises(InvalidFoldFormatException):
            self.crafter.learn_pattern(cls, unfold_func, folds, creases)

    def testFoldPattern(self):
        class Foo(object):
            pass
        cls = Foo
        unfold_func = lambda: None
        folds = 'a=uint:8'
        creases = {}
        self.crafter.learn_pattern(cls, unfold_func, folds, creases)

        foo = Foo()
        foo.a = 127
        data = bitstring.pack('uint:8', foo.a)
        assert self.crafter.fold(foo) == data

    def testFoldUnknownPattern(self):
        class Foo(object):
            pass
        foo = Foo()
        with self.assertRaises(FoldingException):
            self.crafter.fold(foo)

    def testFoldMissingAttribute(self):
        class Foo(object):
            pass
        cls = Foo
        unfold_func = lambda: None
        folds = 'a=uint:8'
        creases = {}
        self.crafter.learn_pattern(cls, unfold_func, folds, creases)

        with self.assertRaises(FoldingException):
            self.crafter.fold(Foo())

    def testFoldInvalidDataType(self):
        class Foo(object):
            pass
        cls = Foo
        unfold_func = lambda: None
        folds = 'a=uint:8'
        creases = {}
        self.crafter.learn_pattern(cls, unfold_func, folds, creases)
        foo = Foo()
        foo.a = 'NotANumber'
        with self.assertRaises(FoldingException):
            self.crafter.fold(foo)

    def testFoldOutOfRangeValue(self):
        class Foo(object):
            pass
        cls = Foo
        unfold_func = lambda: None
        folds = 'a=uint:8'
        creases = {}
        self.crafter.learn_pattern(cls, unfold_func, folds, creases)
        foo = Foo()
        foo.a = 1 << 20
        with self.assertRaises(FoldingException):
            self.crafter.fold(foo)

    def testUnfoldPattern(self):
        class Foo(object):
            pass
        cls = Foo

        def unfold_func(name, instance, **kw):
            instance = instance or Foo()
            instance.a = kw['a']
            return instance
        folds = 'a=uint:8'
        creases = {}
        self.crafter.learn_pattern(cls, unfold_func, folds, creases)

        value = 127
        data = bitstring.pack('uint:8', value)
        foo = self.crafter.unfold(Foo, data)
        assert foo.a == value

    def testUnfoldUnknownPattern(self):
        class Foo(object):
            pass
        with self.assertRaises(UnfoldingException):
            self.crafter.unfold(Foo, None)

    def testUnfoldMissingData(self):
        class Foo(object):
            pass
        cls = Foo

        def unfold_func(name, instance, **kw):
            instance = instance or Foo()
            instance.a = kw['a']
            instance.b = kw['b']
            return instance
        folds = 'a=uint:8, b=uint:8'
        creases = {}
        self.crafter.learn_pattern(cls, unfold_func, folds, creases)

        value = 127
        data = bitstring.pack('uint:8', value)
        with self.assertRaises(UnfoldingException):
            self.crafter.unfold(Foo, data)

    def testUnfoldInvalidDataType(self):
        class Foo(object):
            pass
        cls = Foo

        def unfold_func(name, instance, **kw):
            instance = instance or Foo()
            instance.a = kw['a']
            instance.b = kw['b']
            return instance
        folds = 'a=uint:8, b=uint:8'
        creases = {}
        self.crafter.learn_pattern(cls, unfold_func, folds, creases)

        a, b = 120, 1023
        data = bitstring.pack('uint:8, uint:10', a, b)
        foo = self.crafter.unfold(Foo, data)
        assert foo.a == a
        assert foo.b != b


class PatternTests(unittest.TestCase):
    def setUp(self):
        self.id = unique_id()
        self.other_id = unique_id()
        self.crafter = Crafter(self.id)

    def testPattern(self):
        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8'

        assert hasattr(Foo, 'unfold')
        assert Foo in self.crafter.patterns

    def testPatternNoFolds(self):
        with self.assertRaises(InvalidFoldFormatException):
            @pattern(self.id)
            class Foo(object):
                pass

    def testPatternGlobalCrafter(self):
        @pattern()
        class Foo(object):
            origami_folds = 'a=uint:8'
            pass

        assert hasattr(Foo, 'unfold')
        assert Foo in Crafter('global').patterns

    def testGeneratedUnfoldMethod(self):
        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:8'
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        foo = Foo(127, 128)
        kwargs = {'a': 127, 'b': 128}
        other_foo = Foo.unfold(self.id, None, **kwargs)

        assert foo == other_foo

    def testGeneratedUnfoldReturnsInstance(self):
        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:8'
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        kwargs = {'a': 127, 'b': 128}
        foo = Foo()
        other_foo = Foo.unfold(self.id, foo, **kwargs)

        assert foo is other_foo

    def testMultiCrafterUnfoldWorksForBoth(self):
        @pattern(self.id)
        @pattern(self.other_id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:8'
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        kwargs = {'a': 127, 'b': 128}
        foo = Foo()
        other_foo = Foo()

        foo = Foo.unfold(self.id, foo, **kwargs)
        other_foo = Foo.unfold(self.other_id, foo, **kwargs)

        assert foo == other_foo

    def testPatternUnfoldMissingAttr(self):
        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:8'
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        kwargs = {'a': 127}
        foo = Foo()

        with self.assertRaises(UnfoldingException):
            foo = Foo.unfold(self.id, foo, **kwargs)


class FoldUnfoldTests(unittest.TestCase):
    def setUp(self):
        self.id = unique_id()
        self.other_id = unique_id()
        self.crafter = Crafter(self.id)

    def testSingleCrafter(self):
        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:1'
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        foo = Foo(129, 1)

        data = fold(foo, crafter=self.id)
        other_foo = unfold(Foo, data, crafter=self.id)

        assert foo == other_foo

    def testNameCrease(self):
        counter, a_creases = count_creases(fold=int, unfold=str)

        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:1'
            origami_creases = {'a': a_creases}
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        foo = Foo('129', 1)

        data = fold(foo, crafter=self.id)
        other_foo = unfold(Foo, data, crafter=self.id)

        assert foo == other_foo
        assert counter['fold'] == counter['unfold'] == 1

    def testFormatCrease(self):
        counter, uint8_creases = count_creases(fold=int, unfold=str)

        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:1'
            origami_creases = {'uint:8': uint8_creases}
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        foo = Foo('129', 1)

        data = fold(foo, crafter=self.id)
        other_foo = unfold(Foo, data, crafter=self.id)

        assert foo == other_foo
        assert counter['fold'] == counter['unfold'] == 1

    def testNameCreaseHasPriority(self):
        name_counter, name_creases = count_creases(fold=int, unfold=str)
        fmt_counter, fmt_creases = count_creases(fold=int, unfold=str)

        @pattern(self.id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:1'
            origami_creases = {'a': name_creases, 'uint:8': fmt_creases}
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        foo = Foo('129', 1)

        data = fold(foo, crafter=self.id)
        other_foo = unfold(Foo, data, crafter=self.id)

        assert foo == other_foo
        assert name_counter['fold'] == name_counter['unfold'] == 1
        assert fmt_counter['fold'] == fmt_counter['unfold'] == 0

    def testMultipleCraftersSameFolds(self):
        @pattern(self.id)
        @pattern(self.other_id)
        class Foo(object):
            origami_folds = 'a=uint:8, b=uint:1'
            __init__ = init('a', 'b')
            __eq__ = equals('a', 'b')

        original_foo = Foo(129, 1)

        data = fold(original_foo, crafter=self.id)
        other_data = fold(original_foo, crafter=self.other_id)

        foo = unfold(Foo, data, crafter=self.id)
        other_foo = unfold(Foo, other_data, crafter=self.other_id)

        assert original_foo == foo
        assert foo == other_foo

    def testMultipleCraftersDifferentFolds(self):
        @pattern(self.id)
        @pattern(self.other_id)
        class Foo(object):
            origami_folds = {
                self.id: 'a=uint:8, b=uint:1',
                self.other_id: 'b=uint:1, c=uint:7'
            }
            __init__ = init(*list('abc'))
            __eq__ = equals(*list('abc'))

        original_foo = Foo(129, 1, 100)

        data = fold(original_foo, crafter=self.id)
        other_data = fold(original_foo, crafter=self.other_id)

        foo = unfold(Foo, data, crafter=self.id)
        other_foo = unfold(Foo, other_data, crafter=self.other_id)

        assert foo.a == original_foo.a
        assert foo.b == original_foo.b

        assert other_foo.b == original_foo.b
        assert other_foo.c == original_foo.c

    def testMultipleCraftersUseSameCreases(self):
        counter, b_creases = count_creases(fold=int, unfold=str)

        @pattern(self.other_id)
        @pattern(self.id)
        class Foo(object):
            origami_folds = {
                self.id: 'a=uint:8, b=uint:4',
                self.other_id: 'b=uint:4, c=uint:7'
            }
            origami_creases = {'b': b_creases}
            __init__ = init(*list('abc'))
            __eq__ = equals(*list('abc'))

        original_foo = Foo(129, '12', 100)

        data = fold(original_foo, crafter=self.id)
        other_data = fold(original_foo, crafter=self.other_id)

        foo = unfold(Foo, data, crafter=self.id)
        other_foo = unfold(Foo, other_data, crafter=self.other_id)

        assert foo.a == original_foo.a
        assert foo.b == original_foo.b

        assert other_foo.b == original_foo.b
        assert other_foo.c == original_foo.c

        assert counter['fold'] == counter['unfold'] == 2
