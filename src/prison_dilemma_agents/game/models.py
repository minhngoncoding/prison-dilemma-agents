from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Decision(Enum):
    COOPERATE = "COOPERATE"
    BETRAY = "BETRAY"


@dataclass
class Player:
    player_id: str
    name: str
    score: int = 0


@dataclass
class RoundResult:
    decisions_dict: dict[str, Decision]
    payoffs: dict[str, int]
    round_number: int = 0


@dataclass
class GameState:
    players: list[Player]
    rounds: list[RoundResult]
    max_rounds: int = 20
    current_round: int = 0

    def add_player(self, player: Player):
        self.players.append(player)

    def add_round(self, result: RoundResult):
        self.rounds.append(result)
        self.current_round += 1


class PayoffMatrix:
    CC = 3  # (cooperate, cooperate)
    CD = 0  # (cooperate, defect)
    DC = 5  # (defect, cooperate)
    DD = 1  # (defect, defect)

    @classmethod
    def get_payoff(cls, my_decision: Decision, opponent_decision: Decision) -> int:
        if (
            my_decision == Decision.COOPERATE
            and opponent_decision == Decision.COOPERATE
        ):
            return cls.CC
        elif my_decision == Decision.COOPERATE and opponent_decision == Decision.BETRAY:
            return cls.CD
        elif my_decision == Decision.BETRAY and opponent_decision == Decision.COOPERATE:
            return cls.DC
        else:
            return cls.DD
