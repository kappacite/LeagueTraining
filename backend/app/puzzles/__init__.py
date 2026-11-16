"""Puzzle types. Adding a type = one module in types/ + one entry in each union below."""
from typing import Annotated

from pydantic import Field

from .types.decision import DecisionPuzzle, PublicDecision
from .types.itemization import ItemizationPuzzle, PublicItemization
from .types.scene import PublicScene, ScenePuzzle

Puzzle = Annotated[DecisionPuzzle | ItemizationPuzzle | ScenePuzzle, Field(discriminator="type")]
PublicPuzzle = PublicDecision | PublicItemization | PublicScene
