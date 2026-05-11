#!/usr/bin/env python3

# pylint: disable=C0114, W0107, R0903


class FragmentBase:
    """
    Create and draw fragment of a screen
    """

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.scale = kwargs.get("scale", getattr(parent, "scale", 1))

    def add_fragment(self, **kwargs):
        """
        This part shall be implemented by teh child
        """
        pass
