Origami
=========================================

Origami is a lightweight package to help you serialize (or **fold**) objects into a binary format.

Features:

*   **Easy to add to existing classes** - One class decorator and format string, and you're ready to start folding objects.

*   **Bit-level field sizes** - For an attribute that's always going to be [0,127], why use 4 whole bytes?  Exact control over field sizes with common defaults.

*   **Define common patterns** - With **creases** you can define custom methods for intercepting common attribute folding/unfolding.

    * Is ``uint:17`` a common field?  Add a crease and replace it with ``long_addr`` (or whatever you're using a 17 bit uint for) for more meaningful fold strings!

*   **Only fold attributes you care about** - Don't fold attributes you don't care about.

*   **Fold a class more than one way** - A ``client`` doesn't need the same folded attributes as a ``database``.  High degree of control over how different Crafters fold the same class.

*   **Nesting** - When describing a class's folds, refer to another pattern by its class name to easily nest patterns.

*   **Useful defaults** - The ``@pattern`` decorator automatically generates an appropriate ``unfold`` method on the class for most use-cases, so you don't have to.

*   **Flexible, accessible configuration** - If you want to hand-craft an unfold method, that's fine too.  For more direct control, you can work directly with a Crafter (useful for dynamic code loading/generation)

Installation and Tests
=========================================
Installing with pip is easy::

    pip install origami

Origami is tested against 2.7.3 and 3.3.0 with nose::

    origami$ pip install nose
    origami$ nosetests
    ............................
    ----------------------------------------------------------------------
    Ran 31 tests in 0.008s
    OK

Basic Usage
=========================================

Let's say we've created the following classes::

    class Point(object):
        __slots__ = ['x', 'y']
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

    class Action(object):
        def __init__(self, name=None, point=None):
            self.name = name
            self.point = point
        def do(self):
            pass
        def undo(self):
            pass

Our code is set up in such a way that coordinate values are always between [0, 511].  Let's add folding so we can send these over TCP as packets::

    from origami import pattern, fold, unfold

    @pattern()
    class Point(object):
        origami_folds = 'x=uint:9, y=uint:9'
        __slots__ = ['x', 'y']
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

    @pattern()
    class Action(object):
        origami_folds = 'point=Point, undo=bool'
        def __init__(self, point=None, is_undo=False):
            self.point = point
            self.undo = is_undo

And to use them::

    point = Point(10, 20)
    action = Action(point, True)
    data = fold(action)

    print(data.bytes)

    copy_action = unfold(Action, data)

    print(
        copy_action.point.x,
        copy_action.point.y,
        copy_action.undo
    )

The ``@pattern`` decorator does most of the lifting here, specifying a ``Crafter`` and hooking up the important fields for folding.  ``origami_folds`` describes which attributes to fold, and how to fold them.  ``uint:{n}`` and ``bool`` are built-in bitstring formats, while ``Point`` refers to the recently learned pattern for the Point class.  Note that to use the generated ``unfold`` method from the pattern decorator, the class must support an ``__init__`` method that takes no arguments.

**NOTE:**
 ``unfold`` can take as its first argument either a learned class or an instance of a learned class.  When the class is passed ``unfold(Action, data)`` a new instance is created and returned.  When an instance is passed ``unfold(some_action, data)``, the foldable attributes are unfolded into that object directly and the same object is returned.  This can be useful when creating an instance of the object requires additional setup (such as connecting to a database, or secure credentials that can't be folded).

Multiple patterns
=========================================

The ``@pattern`` decorator takes two optional arguments, ``crafter`` and ``unfold``.  The ``crafter`` argument defaults to 'global' and specifies which Crafter to teach the pattern to.  This allows us to register classes with different crafters, or the same class with multiple crafters.  Since crafters are referred to as strings, it's easy to pass them around in config settings.

Imagine the ``Block`` class for a Minecraft clone, where instances sometimes have bonus loot.  However, we don't want clients to see this flag because malicious users will unroll the packet and know which blocks to mine.  At the same time, the bonus flag should be saved to disk so we don't compute it twice.  We want to fold the same object two different ways, depending on where it's going::

    @pattern('client')
    @pattern('disk')
    class Block(object):
        origami_folds = {
            'client': 'x=uint:32, y=uint:32, type=uint:8',
            'disk':   'x=uint:32, y=uint:32, type=uint:8, bonus=bool'
        }
        def __init__(self, x=0, y=0, bonus=False, type=0):
            # Usual setting of self.{attr} for {attr} in signature



    # And a function to use our blocks
    def update_stale_blocks(self, blocks):

        # Super awesome nested for loop without exception handling!
        for block in blocks:

            client_data = fold(block, crafter='client')
            server_data = fold(block, crafter='disk')

            # We don't even cull nearby players!
            for client in self.clients:
                client.send_block(client_data)


            self.save_block(server_data)

Like pattern, ``fold`` and ``unfold`` take the optional argument ``crafter`` and default to `global`.

Custom ``Unfold`` method
=========================================

By default, the ``@pattern`` decorator will generate an ``unfold`` method for the class.  To work properly, this function requires the class to support an empty constructor.  The following class will not work::

    @pattern()
    class Foo(object):
        origami_folds = 'alive=bool'
        def __init__(self, alive):
            self.alive = alive


In this case, we can tell pattern that we'd like to provide our own ``unfold`` method::

    @pattern(unfold=False)
    class Foo(object):
        origami_folds = 'alive=bool'
        def __init__(self, alive):
            self.alive = alive

        @classmethod
        def unfold(cls, crafter_name, instance, **kwargs):
            instance = instance or cls(False)
            for attr, value in kwargs.items():
                setattr(instance, attr, value)
            return instance

*   ``crafter_name`` is the name of the crafter that is unfolding the object

*   ``instance`` can be an instance of the class, or None

*   ``kwargs`` is a dictionary of {attr -> value} where attr is a string of the attribute to set on the instance.

    * For the class ``Foo`` above, unfolding an instance that was alive would pass ``**kwargs`` as {'alive': ``True``}

Creases
=========================================

Sometimes the bitstring format strings *(such as* ``uint:8`` *)* aren't enough to cover the types of data to fold.  Or, there may be some intermediate action to take whenever an attribute is folded.  Consider::

    block_types = ['Grass', 'Wood', 'Stone', 'Diamond']

    def fold_type(value):
        return block_types.index(value)

    def unfold_type(value):
        return block_types[value]


    @pattern()
    class Block(object):
        origami_folds = 'enabled=bool, type=block-type'
        origami_creases = {
            'block-type': {'fmt': 'uint:2', 'fold': fold_type, 'unfold': unfold_type}
        }
        def  __init__(self, enabled=True, type='Grass'):
            self.enabled = enabled
            self.type = type

Now when we fold a Block, it will use the bitstring format ``bool`` for the enabled field, and our custom functions for any attribute using the ``block-type`` formatter.  These are considered **format creases** since they will be applied to any attribute with a format using that name.

We can also specify **name creases** which are creases that only act on attributes with a matching name.  To achieve the same thing as we have above using a name crease, we would pass::

        origami_creases = {
            'type': {'fmt': 'uint:2', 'fold': fold_type, 'unfold': unfold_type}
        }

That looks almost exactly the same!  Crafters decide if a crease is a name or format crease based on the key for the functions - if the key is found on the left of the equals sign, it's a name crease.  Otherwise, it's a format crease.  Formats and crease names should not contain ``:`` or ``=`` since these are used to delimit the different folds for a pattern.  ``{`` and ``}`` are also reserved,and used for crease format value replacement *(to be implemented)*.  Spaces should not be used.

**NOTES:**

*   Name creases always win out over format creases.  If an attribute is covered by both, **only** the name crease will be used.

*   Creases are defined **for the class** and will be used by any Crafters that know the class.  If you need unique creases for Crafters on the class, read on.

*   'fmt' is only required when the key is a format, and is not already a valid bitstring format.

    * This format crease does not need a fmt key because uint:8 is a bitstring format: ``{'uint:8': {'fold': int, 'unfold': str}}``

    * This format crease **does** need a fmt key, because block-type is not a bitstring format: ``{'block-type': {'fmt': 'uint:8', fold': int, 'unfold': str}}``

    * 'fmt' must refer to a bitstring format - a learned pattern is not valid, since crease fold/unfold methods should take one arg and a pattern can potentially require multiple bitstring formats.

Working directly with a ``Crafter``
=========================================

Sometimes ``pattern`` just doesn't cut it.  For instance, we want to register different creases to each Crafter for a single class.  In this case, it's best to talk directly to the Crafters and explain what we want.

Here's a class using the pattern decorator::

    @pattern()
    class Point(object):
        origami_folds = 'x=uint:9, y=uint:9'
        __slots__ = ['x', 'y']
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

And the equivalent code, explicitly setting the same Crafter up with the class::

    class Point(object):
        __slots__ = ['x', 'y']
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y

    def unfold_point(crafter_name, instance, **kwargs):
        instance = instance or Point()
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        return instance

    cls = Point
    folds = 'x=uint:9, y=uint:9'
    creases = {}
    unfold_func = unfold_point

    crafter = Crafter('global')
    crafter.learn_pattern(cls, unfold_func, folds, creases)

Now, we can pass different creases to different crafters::

    Crafter('foo').learn_pattern(cls, unfold_func, folds, foo_creases)
    Crafter('bar').learn_pattern(cls, unfold_func, folds, bar_creases)

In most cases, this shouldn't be necessary; creases should be more tightly bound to the representation of attributes, which is (usually) a property of the class and not the things describing the class.
