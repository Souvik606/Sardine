"""
super_proxy.py

Defines the SuperProxy runtime object, which represents a reference to the
*parent-class scope* of a model instance. It allows polymorphic child classes to
invoke their parent's overridden methods without triggering infinite recursion.

Usage in Sardine:
    super().method_name(args)
"""


class SuperProxy:
    """
    A runtime proxy that exposes the *parent* model's methods for a given instance.

    When a child class overrides a method from a parent, `super()` (called inside
    a method body) returns a SuperProxy bound to:
      - the current instance (`this`)
      - the owner class of the *currently-executing* method (the child class)

    Calling an attribute on SuperProxy searches the MRO starting from the *parent*
    of the method owner, skipping the child's own definition.

    Attributes:
        instance   : The ModelInstance on which the method will execute.
        owner_class: The Model that owns the currently-running method (the child).
    """

    def __init__(self, instance, owner_class):
        self.instance = instance
        self.owner_class = owner_class
        self.pos_start = instance.pos_start
        self.pos_end = instance.pos_end
        self.context = instance.context

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def copy(self):
        proxy = SuperProxy(self.instance, self.owner_class)
        proxy.set_pos(self.pos_start, self.pos_end)
        proxy.set_context(self.context)
        return proxy

    def get_attr(self, name, calling_context):
        from sards.core.error import AttributeError as SardineAttributeError
        from sards.user_functions import Function

        for parent in self.owner_class.parents:
            method_info = parent.find_method(name)
            if method_info:
                method_node, access_level = method_info

                method = Function(
                    name,
                    method_node.body_node,
                    method_node.param_nodes,
                    False,
                    self.instance,
                    owner_class=parent
                ).set_context(self.instance.context)
                method.set_pos(method_node.pos_start, method_node.pos_end)
                return method, None

        return None, SardineAttributeError(
            self.pos_start, self.pos_end,
            f"No parent of '{self.owner_class.name}' defines method '{name}'",
            calling_context
        )

    def set_attr(self, name, value):
        return self.instance.set_attr(name, value)

    def is_true(self):
        from sards.data_types import Number
        return Number(1), None

    def __repr__(self):
        return f"<super of {self.owner_class.name}>"
