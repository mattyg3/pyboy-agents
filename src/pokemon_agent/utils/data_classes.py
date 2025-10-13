from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# ====== Battle ======
@dataclass
class MoveSet:
    id:str
    name:str
    type:str
    power:int
    accuracy:int
    effect:str
    max_pp:int


@dataclass
class PokemonState:
    name:str
    types: List[str]
    hp: int
    hp_max: int
    status: Optional[str] = None
    moves: List[MoveSet] = field(default_factory=list)

@dataclass
class BattleState:
    turn: int
    player: PokemonState
    enemy: PokemonState
    last_move: Optional[str] = None
    advantage: Optional[str] = None