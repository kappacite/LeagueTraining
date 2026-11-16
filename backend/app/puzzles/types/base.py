from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Grade = Literal["excellent", "correct", "erreur"]
Role = Literal["top", "jungle", "mid", "adc", "support"]
Difficulty = Literal["facile", "moyen", "difficile"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Choice(Strict):
    id: str
    text: str
    grade: Grade
    explanation: str
    items: list[int] = []


class PublicChoice(BaseModel):
    id: str
    text: str
    items: list[int] = []


class PuzzleSummary(BaseModel):
    id: str
    type: str
    role: Role
    difficulty: Difficulty
    title: str


class PublicPuzzleBase(PuzzleSummary):
    """What the browser may see before answering. Separate model, so answers can't leak by accident."""
    patch: str
    context: str
    time_limit: int
    choices: list[PublicChoice]
    stale: bool


class PuzzleBase(Strict):
    id: str
    role: Role
    difficulty: Difficulty
    patch: str
    title: str
    context: str
    time_limit: int = Field(20, ge=5, le=120)
    choices: list[Choice] = Field(min_length=2, max_length=5)
    lesson: str

    @model_validator(mode="after")
    def _check_choices(self):
        ids = [c.id for c in self.choices]
        if len(ids) != len(set(ids)):
            raise ValueError("choice ids must be unique")
        if not any(c.grade == "excellent" for c in self.choices):
            raise ValueError("at least one choice must be 'excellent'")
        return self

    def grade(self, choice_id: str) -> Choice | None:
        return next((c for c in self.choices if c.id == choice_id), None)

    def summary(self) -> PuzzleSummary:
        return PuzzleSummary(**self.model_dump(include=set(PuzzleSummary.model_fields)))

    def _public_fields(self, stale: bool) -> dict:
        return {
            **self.model_dump(include=set(PublicPuzzleBase.model_fields) - {"choices", "stale"}),
            "choices": [PublicChoice(**c.model_dump(include={"id", "text", "items"})) for c in self.choices],
            "stale": stale,
        }

    # Each puzzle type overrides these.
    def public(self, stale: bool) -> PublicPuzzleBase:
        raise NotImplementedError

    def champion_refs(self) -> set[str]:
        return set()

    def item_refs(self) -> set[int]:
        return {i for c in self.choices for i in c.items}

    def summoner_refs(self) -> set[str]:
        return set()
