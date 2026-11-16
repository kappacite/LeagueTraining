"""Animated branching scenes: a graph of up to 3 decisions, each with an intro clip, and endings."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import Grade, PublicPuzzleBase, PuzzleBase, Strict
from .decision import Me, Objective

MAX_DECISIONS = 3
Team = Literal["ally", "enemy"]


class ChampState(Strict):
    champion: str
    team: Team | None = None
    x: float | None = Field(None, ge=0, le=100)
    y: float | None = Field(None, ge=0, le=100)
    me: bool | None = None
    hidden: bool | None = None
    dead: bool | None = None


class WardState(Strict):
    id: str
    team: Team | None = None
    x: float | None = Field(None, ge=0, le=100)
    y: float | None = Field(None, ge=0, le=100)
    removed: bool = False


class Event(Strict):
    type: Literal["ping", "kill", "objective"]
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    label: str = ""


class Keyframe(Strict):
    t: float = Field(ge=0, le=20)
    clock: str | None = None
    champions: list[ChampState] = []
    wards: list[WardState] = []
    objectives: list[Objective] | None = None
    caption: str | None = None
    events: list[Event] = []


Clip = list[Keyframe]


def _check_clip(clip: Clip) -> Clip:
    if not clip:
        raise ValueError("a clip needs at least one keyframe")
    if any(b.t <= a.t for a, b in zip(clip, clip[1:])):
        raise ValueError("keyframe times must be strictly increasing")
    return clip


class SceneChoice(Strict):
    id: str
    text: str
    grade: Grade
    explanation: str
    consequence: Clip
    next: str | None = None
    ending: str | None = None

    @field_validator("consequence")
    @classmethod
    def _clip(cls, v: Clip) -> Clip:
        return _check_clip(v)


class Node(Strict):
    intro: Clip
    question: str = "Que fais-tu ?"
    time_limit: int = Field(15, ge=5, le=120)
    choices: list[SceneChoice] = Field(min_length=2, max_length=4)

    @field_validator("intro")
    @classmethod
    def _clip(cls, v: Clip) -> Clip:
        return _check_clip(v)

    def choice(self, choice_id: str) -> SceneChoice | None:
        return next((c for c in self.choices if c.id == choice_id), None)


class Outcome(Strict):
    drakes: int | None = None
    towers: int | None = None
    gold: int | None = None
    kills: int | None = None
    barons: int | None = None
    heralds: int | None = None
    grubs: int | None = None


class Ending(Strict):
    title: str
    outcome: Outcome
    note: str = ""


class PublicSceneChoice(BaseModel):
    id: str
    text: str


class PublicNode(BaseModel):
    """A node as the browser may see it before answering: no grades, no consequences, no way forward."""
    id: str
    intro: Clip
    question: str
    time_limit: int
    choices: list[PublicSceneChoice]


class PublicScene(PublicPuzzleBase):
    me: Me


class ScenePuzzle(PuzzleBase):
    type: Literal["scene"]
    me: Me
    start: str
    nodes: dict[str, Node]
    endings: dict[str, Ending]
    choices: list = []  # unused: choices live on nodes

    @model_validator(mode="after")
    def _check_choices(self):  # overrides the base check: choices are validated per node
        return self

    @model_validator(mode="after")
    def _check_graph(self):
        if self.start not in self.nodes:
            raise ValueError(f"start '{self.start}' is not a node")
        for nid, node in self.nodes.items():
            ids = [c.id for c in node.choices]
            if len(ids) != len(set(ids)):
                raise ValueError(f"node {nid}: choice ids must be unique")
            if sum(c.grade == "excellent" for c in node.choices) != 1:
                raise ValueError(f"node {nid}: needs exactly one 'excellent' choice")
            for c in node.choices:
                where = f"choice {nid}.{c.id}"
                if (c.next is None) == (c.ending is None):
                    raise ValueError(f"{where}: needs exactly one of next / ending")
                if c.grade == "erreur" and c.ending is None:
                    raise ValueError(f"{where}: an 'erreur' choice must end the scene")
                if c.next is not None and c.next not in self.nodes:
                    raise ValueError(f"{where}: next '{c.next}' is not a node")
                if c.ending is not None and c.ending not in self.endings:
                    raise ValueError(f"{where}: ending '{c.ending}' is not an ending")

        seen_nodes, seen_endings = set(), set()

        def depth(nid: str, stack: tuple) -> int:
            if nid in stack:
                raise ValueError("scene graph has a cycle")
            seen_nodes.add(nid)
            deepest = 0
            for c in self.nodes[nid].choices:
                if c.next:
                    deepest = max(deepest, depth(c.next, stack + (nid,)))
                else:
                    seen_endings.add(c.ending)
            return 1 + deepest

        if depth(self.start, ()) > MAX_DECISIONS:
            raise ValueError(f"a path has more than {MAX_DECISIONS} decisions")
        for nid in self.nodes.keys() - seen_nodes:
            raise ValueError(f"node '{nid}' is unreachable")
        for eid in self.endings.keys() - seen_endings:
            raise ValueError(f"ending '{eid}' is unreachable")

        first = self.nodes[self.start].intro[0].champions
        mine = [c for c in first if c.me]
        if len(mine) != 1 or mine[0].champion != self.me.champion:
            raise ValueError("first keyframe of the start node must place exactly one 'me' champion, "
                             "equal to me.champion")
        return self

    # --- views ---
    def public(self, stale: bool) -> PublicScene:
        return PublicScene(**self._public_fields(stale), me=self.me)

    def public_node(self, node_id: str) -> PublicNode:
        n = self.nodes[node_id]
        return PublicNode(id=node_id, intro=n.intro, question=n.question, time_limit=n.time_limit,
                          choices=[PublicSceneChoice(id=c.id, text=c.text) for c in n.choices])

    # --- graph helpers ---
    def optimal_path(self) -> list[tuple[str, str]]:
        path, nid = [], self.start
        while nid:
            best = next(c for c in self.nodes[nid].choices if c.grade == "excellent")
            path.append((nid, best.id))
            nid = best.next
        return path

    def ending_of(self, path: list[tuple[str, str]]) -> str | None:
        nid, cid = path[-1]
        return self.nodes[nid].choice(cid).ending

    def clips_for(self, path: list[tuple[str, str]]) -> list[Clip]:
        clips = []
        for nid, cid in path:
            node = self.nodes[nid]
            clips += [node.intro, node.choice(cid).consequence]
        return clips

    # --- refs checked against Data Dragon ---
    def _all_clips(self):
        for node in self.nodes.values():
            yield node.intro
            for c in node.choices:
                yield c.consequence

    def champion_refs(self) -> set[str]:
        return {self.me.champion} | {c.champion for clip in self._all_clips() for kf in clip for c in kf.champions}

    def item_refs(self) -> set[int]:
        return set(self.me.items)

    def summoner_refs(self) -> set[str]:
        return set(self.me.summoners)
