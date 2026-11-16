from typing import Literal

from pydantic import Field, model_validator

from .base import PublicPuzzleBase, PuzzleBase, Strict


class Me(Strict):
    champion: str
    hp: int = Field(ge=0, le=100)
    mana: int | None = Field(None, ge=0, le=100)
    gold: int = Field(ge=0)
    summoners: list[str] = []
    items: list[int] = []


class ScenePlacement(Strict):
    champion: str
    team: Literal["ally", "enemy"]
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    me: bool = False
    last_seen: int | None = None  # seconds since last seen; None = visible


class Ward(Strict):
    team: Literal["ally", "enemy"]
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)


class Objective(Strict):
    type: str
    spawn_in: int | None = None  # seconds; None = alive


class Scene(Strict):
    champions: list[ScenePlacement]
    wards: list[Ward] = []
    objectives: list[Objective] = []


class PublicDecision(PublicPuzzleBase):
    me: Me
    scene: Scene


class DecisionPuzzle(PuzzleBase):
    type: Literal["decision"]
    me: Me
    scene: Scene

    @model_validator(mode="after")
    def _check_me(self):
        mine = [c for c in self.scene.champions if c.me]
        if len(mine) != 1:
            raise ValueError("exactly one scene champion must have me: true")
        if mine[0].champion != self.me.champion:
            raise ValueError("the scene champion with me: true must be me.champion")
        return self

    def public(self, stale: bool) -> PublicDecision:
        return PublicDecision(**self._public_fields(stale), me=self.me, scene=self.scene)

    def champion_refs(self) -> set[str]:
        return {self.me.champion} | {c.champion for c in self.scene.champions}

    def item_refs(self) -> set[int]:
        return super().item_refs() | set(self.me.items)

    def summoner_refs(self) -> set[str]:
        return set(self.me.summoners)
