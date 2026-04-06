import pytest
from prison_dilemma_agents.game.models import (
    Decision,
    Player,
    RoundResult,
    GameState,
    PayoffMatrix,
)


class TestDecision:
    def test_cooperate_value(self):
        assert Decision.COOPERATE.value == "COOPERATE"

    def test_defect_value(self):
        assert Decision.BETRAY.value == "BETRAY"


class TestPlayer:
    def test_create_player(self):
        player = Player(player_id="p1", name="Alice")
        assert player.player_id == "p1"
        assert player.name == "Alice"
        assert player.score == 0

    def test_player_with_score(self):
        player = Player(player_id="p1", name="Bob", score=10)
        assert player.score == 10


class TestPayoffMatrix:
    def test_mutual_cooperation(self):
        assert PayoffMatrix.get_payoff(Decision.COOPERATE, Decision.COOPERATE) == 3

    def test_mutual_defection(self):
        assert PayoffMatrix.get_payoff(Decision.BETRAY, Decision.BETRAY) == 1

    def test_cooperate_vs_defect(self):
        assert PayoffMatrix.get_payoff(Decision.COOPERATE, Decision.BETRAY) == 0

    def test_defect_vs_cooperate(self):
        assert PayoffMatrix.get_payoff(Decision.BETRAY, Decision.COOPERATE) == 5


class TestRoundResult:
    def test_create_round_result(self):
        result = RoundResult(
            round_number=1,
            decisions={"p1": Decision.COOPERATE, "p2": Decision.BETRAY},
            payoffs={"p1": 0, "p2": 5},
        )
        assert result.round_number == 1
        assert result.decisions["p1"] == Decision.COOPERATE
        assert result.payoffs["p2"] == 5


class TestGameState:
    def test_add_player(self):
        state = GameState([], [])
        player = Player(player_id="p1", name="Alice")
        state.add_player(player)
        assert len(state.players) == 1

    def test_add_round_updates_score(self):
        state = GameState([], [])
        state.add_player(Player(player_id="p1", name="Alice"))
        state.add_player(Player(player_id="p2", name="Bob"))

        round1 = RoundResult(
            round_number=1,
            decisions={"p1": Decision.COOPERATE, "p2": Decision.COOPERATE},
            payoffs={"p1": 3, "p2": 3},
        )
        state.add_round(round1)

        round2 = RoundResult(
            round_number=2,
            decisions={"p1": Decision.BETRAY, "p2": Decision.BETRAY},
            payoffs={"p1": 1, "p2": 1},
        )
        state.add_round(round2)
        assert state.current_round == 2
