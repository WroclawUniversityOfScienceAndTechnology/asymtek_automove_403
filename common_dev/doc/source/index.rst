=========================================================
Project Documentation
=========================================================
 .. toctree::
   :maxdepth: 2
   :caption: Contents

   main_page

Source code
==================
.. autosummary::
   :toctree: _autosummary
   :caption: Source code:
   :template: custom-module-template.rst
   :recursive:

      src

Test code
==================
.. autosummary::
   :toctree: _autosummary
   :caption: Test code:
   :template: custom-module-template.rst
   :recursive:

      test


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Diagram example
==================
You can easily embed diagrams in the documentation!
TODO! Check if planUML will work here as well

.. graphviz::

   digraph foo {
      "bar" -> "baz";
   }