from typing import Literal

from pydantic import Field

from .base import PublicPuzzleBase, PuzzleBase, Strict


class ItemMe(Strict):
    champion: str
    level: int = Field(ge=1, le=18)
    gold: int = Field(ge=0)
    items: list[int] = []


class Enemy(Strict):
    champion: str
    items: list[int] = []


class PublicItemization(PublicPuzzleBase):
    me: ItemMe
    allies: list[str]
    enemies: list[Enemy]


class ItemizationPuzzle(PuzzleBase):
    type: Literal["itemization"]
    me: ItemMe
    allies: list[str] = []
    enemies: list[Enemy]

    def public(self, stale: bool) -> PublicItemization:
        return PublicItemization(**self._public_fields(stale), me=self.me, allies=self.allies, enemies=self.enemies)

    def champion_refs(self) -> set[str]:
        return {self.me.champion, *self.allies} | {e.champion for e in self.enemies}

    def item_refs(self) -> set[int]:
        return super().item_refs() | set(self.me.items) | {i for e in self.enemies for i in e.items}
