"""Puzzle types. Adding a type = one module in types/ + one entry in each union below."""
from typing import Annotated

from pydantic import Field

from .types.decision import DecisionPuzzle, PublicDecision
from .types.itemization import ItemizationPuzzle, PublicItemization

Puzzle = Annotated[DecisionPuzzle | ItemizationPuzzle, Field(discriminator="type")]
PublicPuzzle = PublicDecision | PublicItemization
