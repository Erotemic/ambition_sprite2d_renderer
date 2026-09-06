"""Turning HAND-DRAWN SVGs into rigged ones, reproducibly.

Two of Ambition's characters are drawn by a person in Inkscape and rigged by a
program: the file under ``assets/`` is the art, and the file under
``data/characters/<name>/`` is that art with a bone catalog and marker layer
built onto it. This package is the second half.

⛔⛔ IT LIVED IN AN UNTRACKED SCRATCH DIRECTORY, and that made the rigs
UNREPRODUCIBLE ARTIFACTS: they were committed, the program that produced them
was not, and regenerating one on another machine was impossible. That is the
same defect as authoring art into a generated file -- one level up -- and it is
why the Officer's hand-drawn torsos could be silently destroyed by a rebuild
nobody could run.

⭐ THE SOURCE IS THE ART FILE. Anything a person draws belongs in ``assets/``;
anything here only carries it across and computes what a skeleton needs. A
generator that INVENTS art (the side torso's shell) is a stopgap for a shape
nobody has drawn yet, and it must leave alone anything the source already
authors -- see ``humanoid_torsos``.
"""
