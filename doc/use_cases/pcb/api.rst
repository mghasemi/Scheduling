PCB use-case API
================

The PCB helpers are optional and live in
``scheduling.use_cases.pcb``. Install their dependencies using the
``pcb`` extra. The ``scheduling.pcb`` module is retained only for backwards
compatibility.

``Perimeter`` accepts a CSV or Excel export with the fields used by the
historical analysis. In addition to supplying a compatible input file, set
``cache_path`` if you want to control where the generated synthetic-call cache
is stored.

``Primary911`` requires the original call-log export and has a separate
``cache_path`` parameter for its normalized output. Dataset schemas and
preprocessing are specific to this use case.

.. automodule:: scheduling.use_cases.pcb
   :members:
