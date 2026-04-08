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
    """Result of a single round within a match."""

    decisions: dict[str, Decision]
    payoffs: dict[str, int]
    round_number: int = 0
    # Reasoning for each player's decision (optional, for LLM players)
    reasoning: dict[str, str] = field(default_factory=dict)


@dataclass
class MatchResult:
    """Result of a single match between two players."""

    player1_id: str
    player2_id: str
    player1_strategy: str
    player2_strategy: str
    player1_total_score: int = 0
    player2_total_score: int = 0
    rounds_played: int = 0
    round_history: list[RoundResult] = field(default_factory=list)
    winner: str | None = None  # "player1", "player2", or "draw"


@dataclass
class TournamentRound:
    """One round of the tournament where ALL pairs play simultaneously."""

    round_number: int
    # List of (player1_id, player2_id, player1_decision, player2_decision, p1_payoff, p2_payoff, p1_reasoning, p2_reasoning)
    match_results: list[tuple] = field(default_factory=list)

    def add_match_result(
        self,
        player1_id: str,
        player2_id: str,
        p1_decision: Decision,
        p2_decision: Decision,
        p1_payoff: int,
        p2_payoff: int,
        p1_reasoning: str = "",
        p2_reasoning: str = "",
    ):
        self.match_results.append(
            (
                player1_id,
                player2_id,
                p1_decision,
                p2_decision,
                p1_payoff,
                p2_payoff,
                p1_reasoning,
                p2_reasoning,
            )
        )


@dataclass
class TournamentState:
    """State of a tournament with all matches."""

    players: list[Player] = field(default_factory=list)
    matches: list[MatchResult] = field(default_factory=list)
    tournament_rounds: list[TournamentRound] = field(default_factory=list)
    rounds_per_match: int = 10
    current_match_index: int = 0

    def add_match(self, match_result: MatchResult):
        self.matches.append(match_result)

    def add_tournament_round(self, tournament_round: TournamentRound):
        self.tournament_rounds.append(tournament_round)

    def get_player_score(self, player_id: str) -> int:
        """Get total score across all matches for a player."""
        total = 0
        for match in self.matches:
            if match.player1_id == player_id:
                total += match.player1_total_score
            elif match.player2_id == player_id:
                total += match.player2_total_score
        return total

    def get_player_total_rounds(self, player_id: str) -> int:
        """Get total rounds played by a player across all matches."""
        total = 0
        for match in self.matches:
            if match.player1_id == player_id or match.player2_id == player_id:
                total += match.rounds_played
        return total

    def get_winner(self) -> list[str]:
        """Get list of player IDs with highest total score."""
        scores = {}
        for player in self.players:
            scores[player.player_id] = self.get_player_score(player.player_id)

        if not scores:
            return []

        max_score = max(scores.values())
        return [pid for pid, score in scores.items() if score == max_score]

    @property
    def total_matches(self) -> int:
        """Total number of matches in tournament (n*(n-1) for round robin)."""
        n = len(self.players)
        return n * (n - 1)

    @property
    def matches_completed(self) -> int:
        return len(self.matches)

    @property
    def progress_percentage(self) -> float:
        if self.total_matches == 0:
            return 0.0
        return (self.matches_completed / self.total_matches) * 100


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

    # ------------------------------------------------------------------
    # Helper methods for accessing game state
    # ------------------------------------------------------------------

    def get_score(self, player_id: str) -> int:
        """Get cumulative score for a player."""
        return sum(r.payoffs.get(player_id, 0) for r in self.rounds)

    def get_opponent_id(self, player_id: str) -> Optional[str]:
        """Get opponent's player ID (assumes 2 players)."""
        for p in self.players:
            if p.player_id != player_id:
                return p.player_id
        return None

    def get_opponent_last_move(self, player_id: str) -> Optional[Decision]:
        """Get opponent's most recent decision."""
        if not self.rounds:
            return None
        opponent_id = self.get_opponent_id(player_id)
        if not opponent_id:
            return None
        return self.rounds[-1].decisions.get(opponent_id)

    def get_rounds_remaining(self) -> int:
        """Number of rounds left."""
        return self.max_rounds - len(self.rounds)


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
