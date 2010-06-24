# Copyright (c) 2010 Jonathan M. Lange. See LICENSE for details.


class MonkeyPatcher(object):
    """
    Cover up attributes with new objects. Neat for monkey-patching things for
    unit-testing purposes.
    """

    def __init__(self, *patches):
        # List of patches to apply in (obj, name, value).
        self._patches_to_apply = []
        # List of the original values for things that have been patched.
        # (obj, name, value) format.
        self._originals = []
        for patch in patches:
            self.add_patch(*patch)

    def add_patch(self, obj, name, value):
        """
        Add a patch so that the attribute C{name} on C{obj} will be assigned to
        C{value} when C{patch} is called or during C{run_with_patches}.

        You can restore the original values with a call to restore().
        """
        self._patches_to_apply.append((obj, name, value))

    def _already_patched(self, obj, name):
        """
        Has the C{name} attribute of C{obj} already been patched by this
        patcher?
        """
        for o, n, v in self._originals:
            if (o, n) == (obj, name):
                return True
        return False

    def patch(self):
        """
        Apply all of the patches that have been specified with L{add_patch}.
        Reverse this operation using L{restore}.
        """
        for obj, name, value in self._patches_to_apply:
            if not self._already_patched(obj, name):
                self._originals.append((obj, name, getattr(obj, name)))
            setattr(obj, name, value)

    def restore(self):
        """
        Restore all original values to any patched objects.
        """
        while self._originals:
            obj, name, value = self._originals.pop()
            setattr(obj, name, value)

    def run_with_patches(self, f, *args, **kw):
        """
        Apply each patch already specified. Then run the function f with the
        given args and kwargs. Restore everything when done.
        """
        self.patch()
        try:
            return f(*args, **kw)
        finally:
            self.restore()
