Origami
========================================================

*(Tested against 3.4)*

Origami is a lightweight package to help you serialize (or **fold**) objects into a binary format.

Features:

*   **Easy to add to existing classes** - One class decorator and format string, and you're ready to start folding objects.

*   **Bit-level field sizes** - For an attribute that's always going to be [0,127], why use 4 whole bytes?  Exact control over field sizes with common defaults.

*   **Define common patterns** - With **creases** you can define custom methods for intercepting common attribute folding/unfolding.

    * Is ``uint:17`` a common field?  Add a crease and replace it with ``long_addr`` (or whatever you're using a 17 bit uint for) for more meaningful fold strings!

*   **Only fold attributes you care about**

*   **Fold a class more than one way** - A ``client`` doesn't need the same folded attributes as a ``database``.  High degree of control over how different Crafters fold the same class.

*   **Nesting** - When describing a class's folds, refer to another pattern by its class name to easily nest patterns.

*   **Useful defaults** - The ``@pattern`` decorator automatically generates an appropriate ``unfold`` method on the class for most use-cases, so you don't have to.

*   **Flexible, accessible configuration** - If you want to hand-craft an unfold method, that's fine too.  For more direct control, you can work directly with a Crafter (useful for dynamic code loading/generation)

Installation
========================================================

::

    pip install origami

Basic Usage
========================================================

Let's say we've created the following classes for our collaborative editing tool::

    class Point(object):
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

    class Action(object):
        def __init__(self, id=None, point=None):
            self.id = id
            self.point = point

Our code is set up in such a way that coordinate values are always between [0, 511].  We're using TCP to sync actions, so let's add some folding::

    from origami import pattern, fold, unfold

    @pattern
    class Point(object):
        folds = 'x=uint:9, y=uint:9'
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

    @pattern
    class Action(object):
        folds = 'id=uint:32, point=Point'
        def __init__(self, id=None, point=None):
            self.id = id
            self.point = point

And to use them::

    point = Point(10, 20)
    action = Action(next_id(), point)
    action_data = fold(action)

    print(action_data.bytes)

    copy_action = unfold(action_data, Action)

    print(
        copy_action.point.x,
        copy_action.point.y,
        copy_action.undo
    )

    server.send_action(action_data)

The ``@pattern`` decorator does most of the lifting here, specifying a ``Crafter`` and hooking up the important fields for folding.  ``folds`` describes which attributes to fold, and how to fold them.  ``uint:{n}`` and ``bool`` are built-in bitstring formats, while ``Point`` refers to the recently learned pattern for the Point class.  Note that to use the generated ``unfold`` method from the pattern decorator, the class must support an ``__init__`` method that takes no arguments.

**NOTE:**
 ``unfold`` can take as its second argument either a learned class or an instance of a learned class.  When the class is passed ``unfold(data, Action)`` a new instance is created and returned.  When an instance is passed ``unfold(data, empty_action)``, the foldable attributes are unfolded into that object directly and the same object is returned.  This can be useful when creating an instance of the object requires additional setup (such as connecting to a database, or secure credentials that can't be folded).

What data types are supported?
========================================================
Origami uses bitstring under the hood, so any format must eventually reduce to one that bitstring understands (`formats <http://pythonhosted.org/bitstring/creation.html#using-the-constructor>`_).  See `Nesting`_ for building more complex structures.

Why not just use ``Pickle``?
========================================================
As always, the answer is "it depends".  Origami's primary advantage over pickle is the packed data's size, and the ability to selectively pack attributes without writing repetitive ``__getstate__`` and ``__setstate__`` functions.

Pickle has the following advantages over origami:

* **Simplicity** - While origami aims to have low code overhead, it doesn't get much lower than pickle's zero.  For the set of values which origami covers, pickle requires no additional code beyond what you'd normally write for your class.

* **Built-in module** - Pickle comes with python.  Origami currently depends on bitstring.

* **Pickle ALL the things** - Pickle can pack any python class, and handles recursive objects and object sharing like a champ.  Origami supports a small subset of data types, and handles neither recursion or sharing.

Origami has the following advantages over pickle:

* **Packed Size** - Origami offers serious space savings over pickle for basic objects.  See Appendix A for a (contrived) comparison.

* **Consise partial attribute folding** - Origami offers the ability to fold select attributes, when all values aren't needed/ shouldn't be distributed.  This is also possible with pickle by defining ``___getstate__`` and ``__setstate__`` functions, but this feels a bit heavy-weight compared to origami's fold strings (see `Multiple patterns`_)

* **Multi-format folding** - Related to the previous, origami allows the same class to be folded differently for different consumers.

* **Python-independent format** - Origami (more directly, the underlying use of bitstring) does not depend on python-specific behavior for (un)folding values.

Multiple patterns
========================================================

The ``@pattern`` decorator takes two optional arguments, ``crafter`` and ``unfold``.  The ``crafter`` argument defaults to 'global' and specifies which Crafter to teach the pattern to.  This allows us to register classes with different crafters, or the same class with multiple crafters.  Since crafters are referred to as strings, it's easy to pass them around in config settings.

Imagine the ``Block`` class for a Minecraft clone, where instances sometimes have bonus loot.  However, we don't want clients to see this flag because malicious users will unroll the packet and know which blocks to mine.  At the same time, the bonus flag should be saved to disk so we don't compute it twice.  We want to fold the same object two different ways, depending on where it's going::

    @pattern('client')
    @pattern('disk')
    class Block(object):
        folds = {
            'client': 'x=uint:32, y=uint:32, type=uint:8',
            'disk':   'x=uint:32, y=uint:32, type=uint:8, bonus=bool'
        }
        def __init__(self, x=0, y=0, bonus=False, type=0):
            # Usual setting of self.{attr} for {attr} in signature


    # And a function to use our blocks
    def update_stale_blocks(self, blocks):
        for block in blocks:
            client_data = fold(block, crafter='client')
            server_data = fold(block, crafter='disk')

            self.save_block(server_data)
            for client in self.clients:
                client.send_block(client_data)


Like pattern, ``fold`` and ``unfold`` take the optional argument ``crafter`` and default to `global`.

Nesting
========================================================

Origami's nesting allows complex structures to be built on top of the primitives that bitstring understands.
::

    from origami import pattern

    @pattern
    class Color(object):
        folds = 'r=uint:8, g=uint:8, b=uint:8, a=uint:8'
        def __init__(self, r=0, g=0, b=0, a=0):
            # Set self.[rgba]

Now, we can (un)fold an arbitrary palette without needing to remember how each color is (un)folded::

    @pattern
    class Palette(object):
        folds = 'primary=Color, secondary=Color'
        def __init__(self, primary=None, secondary=None):
            # Set self.[primary, secondary]


Custom ``Unfold`` method
========================================================

By default, the ``@pattern`` decorator will generate an ``unfold`` method for the class.  To work properly, this function expects the class to support an empty constructor.  The following class will not work::

    @pattern
    class Foo(object):
        folds = 'alive=bool'
        def __init__(self, alive):
            self.alive = alive


In this case, we can tell pattern that we'd like to provide our own ``unfold`` method::

    @pattern(unfold=False)
    class Foo(object):
        folds = 'alive=bool'
        def __init__(self, alive):
            self.alive = alive

        @classmethod
        def unfold(cls, crafter_name, instance, **kwargs):
            instance = instance or cls(False)
            for attr, value in kwargs.items():
                setattr(instance, attr, value)
            return instance

Where:

*   ``crafter_name`` is the name of the crafter that is unfolding the object

*   ``instance`` can be an instance of the class, or None

*   ``kwargs`` is a dictionary of {attr -> value} where attr is a string of the attribute to set on the instance.

    * For the class ``Foo`` above, unfolding an instance that was alive would pass ``**kwargs`` as {'alive': ``True``}

Creases
========================================================

Sometimes the bitstring format strings *(such as uint:8)* aren't enough to cover the types of data to fold.  Or, there may be some intermediate action to take whenever an attribute is folded.  Consider a block type, which is one of four values.  We can serialize this as an int, but want to interact with it as its appropriate type string::

    types = ['Grass', 'Wood', 'Stone', 'Diamond']

    def fold_block(value):
        return block_types.index(value)

    def unfold_block(value):
        return block_types[value]


    @pattern
    class Block(object):
        folds = 'enabled=bool, type=block'
        creases = {
          'block': {
            'fmt': 'uint:2',
            'fold': fold_block,
            'unfold': unfold_block
          }
        }
        def  __init__(self, enabled=True, type='Grass'):
            self.enabled = enabled
            self.type = type

Now when we fold a Block, it will use the bitstring format ``bool`` for the enabled field, and our custom functions for any attribute using the ``block`` formatter.  These are considered **format creases** since they will be applied to any attribute with a format using that name.

We can also specify **name creases** which are creases that only act on attributes with a matching name.  To achieve the same thing as we have above using a name crease, we would instead pass::

        creases = {
            'type': {'fmt': 'uint:2', 'fold': fold_block, 'unfold': unfold_block}
        }

That looks almost exactly the same!  Crafters decide if a crease is a name or format crease based on the key for the functions - if the key is found on the left of the equals sign, it's a name crease.  Otherwise, it's a format crease.  Formats and crease names should not contain ``:`` or ``=`` since these are used to delimit the different folds for a pattern.  ``{`` and ``}`` are also reserved.  Spaces should not be used (they will be stripped off).

**NOTES:**

*   Name creases always win out over format creases.  If an attribute is covered by both, **only** the name crease will be used.

*   Creases are defined **for the class** and will be used by any Crafters that know the class.  If you need unique creases for Crafters on the class, read on.

*   'fmt' is only required when the key is a format, and is not already a valid bitstring format.

    * This format crease does not need a fmt key because uint:8 is a bitstring format: ``{'uint:8': {'fold': int, 'unfold': str}}``

    * This format crease **does** need a fmt key, because block is not a bitstring format: ``{'block': {'fmt': 'uint:8', fold': int, 'unfold': str}}``

    * 'fmt' must refer to a bitstring format - a learned pattern is not valid, since crease fold/unfold methods should take one arg, while a pattern can potentially require multiple bitstring formats.

Working directly with a ``Crafter``
========================================================

Sometimes ``pattern`` just doesn't cut it.  For instance, we want to register different creases to each Crafter for a single class.  In this case, it's best to talk directly to the Crafters and explain what we want.

Here's a class using the pattern decorator::

    @pattern
    class Point(object):
        folds = 'x=uint:9, y=uint:9'
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

And the equivalent code, explicitly setting the same Crafter up with the class::

    class Point(object):
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

    def unfold_func(crafter_name, instance, **kwargs):
        instance = instance or Point()
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        return instance

    folds = 'x=uint:9, y=uint:9'
    creases = {}

    Crafter('global').learn_pattern(Point, unfold_func, folds, creases)

Now, we can pass different folds or creases to different crafters::

    Crafter('foo').learn_pattern(Point, unfold_func, folds, foo_creases)
    Crafter('bar').learn_pattern(Point, unfold_func, folds, bar_creases)

In most cases, different creases shouldn't be necessary; creases should be more tightly bound to the representation of attributes, which is (usually) a property of the class and not the things describing the class.

Appendix A: Size comparison between origami and pickle
========================================================
Origami (2 bytes)::

    from origami import pattern, fold

    @pattern
    class Point(object):
        folds = 'x=uint:8, y=uint:8'
        def __init__(self, x=0, y=0):
            self.x, self.y = x, y

    p = Point(4, 5)
    print fold(p).bytes  # '\x04\x05'

Pickle (111 bytes, optimized 87 bytes)::

    from pickle import dumps
    from pickletools import optimize

    class Point(object):
        def __init__(self, x=0, y=0):
            self.x, self.y = x, y

    p = Point(4, 5)
    pp = dumps(p)
    opp = optimize(pp)

    print len(pp)  # 111
    print len(opp)  # 87
