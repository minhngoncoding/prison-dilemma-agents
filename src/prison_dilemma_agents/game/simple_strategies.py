import random

from prison_dilemma_agents.game.engine import DecisionMaker
from prison_dilemma_agents.game.models import Decision, GameState


class AlwaysCooperate(DecisionMaker):
    """Always cooperate regardless of game state."""

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        return Decision.COOPERATE


class AlwaysBetray(DecisionMaker):
    """Always betray regardless of game state."""

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        return Decision.BETRAY


class RandomDecisionMaker(DecisionMaker):
    """Randomly choose cooperate or betray."""

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        return random.choice([Decision.COOPERATE, Decision.BETRAY])


class TitForTat(DecisionMaker):
    """
    Start with cooperate, then mirror opponent's last move.
    If multiple opponents, use most common previous decision.
    """

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        if not game_state.rounds:
            return Decision.COOPERATE

        last_round = game_state.rounds[-1]
        opponent_decisions = [
            dec for pid, dec in last_round.decisions.items() if pid != player_id
        ]

        if not opponent_decisions:
            return Decision.COOPERATE

        cooperate_count = sum(1 for d in opponent_decisions if d == Decision.COOPERATE)
        betray_count = len(opponent_decisions) - cooperate_count

        return (
            Decision.COOPERATE if cooperate_count >= betray_count else Decision.BETRAY
        )


class SuspiciousTitForTat(DecisionMaker):
    """
    Start with betray, then mirror opponent's last move.
    More aggressive variant of TitForTat.
    """

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        if not game_state.rounds:
            return Decision.BETRAY

        last_round = game_state.rounds[-1]
        opponent_decisions = [
            dec for pid, dec in last_round.decisions.items() if pid != player_id
        ]

        if not opponent_decisions:
            return Decision.BETRAY

        cooperate_count = sum(1 for d in opponent_decisions if d == Decision.COOPERATE)
        betray_count = len(opponent_decisions) - cooperate_count

        return Decision.COOPERATE if cooperate_count > betray_count else Decision.BETRAY
