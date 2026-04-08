"""
Game Engine for Prisoner's Dilemma.

Handles game mechanics: collecting decisions, calculating payoffs, tracking state.
"""

import asyncio
import itertools
from typing import Protocol

from prison_dilemma_agents.game.models import (
    Decision,
    GameState,
    MatchResult,
    PayoffMatrix,
    Player,
    RoundResult,
    TournamentRound,
    TournamentState,
)


class DecisionMaker(Protocol):
    """
    Protocol for objects that can make game decisions.

    Any class implementing this protocol can participate in the game.
    Example implementations: RandomDecisionMaker, AlwaysCooperate, TitForTat, LLMPlayer
    """

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        """
        Decide COOPERATE or BETRAY based on game state.

        Args:
            game_state: Current game state including history
            player_id: ID of the player making the decision

        Returns:
            Decision.COOPERATE or Decision.BETRAY
        """


class GameEngine:
    """
    Manages game flow: collects decisions, calculates payoffs, tracks state.
    """

    def __init__(self, payoff_matrix: PayoffMatrix = None):
        self.payoff_matrix = payoff_matrix or PayoffMatrix()

    async def play_round(
        self,
        game_state: GameState,
        decision_makers: list[DecisionMaker],
        capture_reasoning: bool = False,
    ) -> RoundResult:
        """
        Play a single round of the game.

        Args:
            game_state: Current game state
            decision_makers: List of decision makers (one per player, in same order)
            capture_reasoning: Whether to capture reasoning from LLM players

        Returns:
            RoundResult with decisions and payoffs
        """
        decisions = {}
        reasoning = {}

        for i, player in enumerate(game_state.players):
            maker = decision_makers[i]
            decision = await maker.decide(game_state, player.player_id)
            decisions[player.player_id] = decision

            # Capture reasoning if available (for LLM players)
            if capture_reasoning and hasattr(maker, "get_reasoning"):
                reasoning[player.player_id] = maker.get_reasoning()

        payoffs = self._calculate_payoffs(decisions)

        result = RoundResult(
            decisions=decisions,
            payoffs=payoffs,
            round_number=game_state.current_round + 1,
            reasoning=reasoning,
        )

        game_state.add_round(result)
        return result

    def _calculate_payoffs(self, decisions: dict[str, Decision]) -> dict[str, int]:
        """Calculate payoffs for all players based on their decisions."""
        player_ids = list(decisions.keys())
        payoffs = {pid: 0 for pid in player_ids}

        for i, player_id in enumerate(player_ids):
            my_decision = decisions[player_id]
            for j, opponent_id in enumerate(player_ids):
                if i == j:
                    continue
                opponent_decision = decisions[opponent_id]
                payoff = self.payoff_matrix.get_payoff(my_decision, opponent_decision)
                payoffs[player_id] += payoff

        return payoffs

    def is_game_over(self, game_state: GameState) -> bool:
        """Check if the game has ended."""
        return game_state.current_round >= game_state.max_rounds

    def get_winner(self, game_state: GameState) -> str | None:
        """Determine the winner based on final scores. Returns None for tie."""
        scores = {}
        for player in game_state.players:
            total = sum(r.payoffs.get(player.player_id, 0) for r in game_state.rounds)
            scores[player.player_id] = total

        if len(scores) < 2:
            return None

        max_score = max(scores.values())
        min_score = min(scores.values())

        # If tied, return None
        if max_score == min_score:
            return None

        # Return player with highest score
        for pid, score in scores.items():
            if score == max_score:
                return pid

        return None


class Tournament:
    """
    Manages a tournament where each player competes against all other players.

    Round-robin format: in each round, ALL pairs play simultaneously.
    - With 3 players: round 1 has (1vs2, 1vs3, 2vs3)
    - With 4 players: round 1 has 6 matches playing in parallel

    After all rounds complete, each pair has played the specified number of rounds.
    """

    def __init__(self, engine: GameEngine = None):
        self.engine = engine or GameEngine()

    async def play_tournament_round(
        self,
        game_states: dict[tuple[str, str], GameState],
        decision_makers: dict[str, DecisionMaker],
        match_pairs: list[tuple[str, str]],
        round_number: int,
    ) -> TournamentRound:
        """
        Play ONE round where ALL match pairs play simultaneously.

        Args:
            game_states: Dict mapping (p1_id, p2_id) to GameState
            decision_makers: Dict mapping player_id to DecisionMaker
            match_pairs: List of (p1_id, p2_id) tuples
            round_number: Current round number (1-indexed)

        Returns:
            TournamentRound with all match results for this round
        """
        tournament_round = TournamentRound(round_number=round_number)

        # Play all matches in parallel
        tasks = []
        for p1_id, p2_id in match_pairs:
            game_state = game_states[(p1_id, p2_id)]
            decision_makers_pair = [decision_makers[p1_id], decision_makers[p2_id]]
            # Pass capture_reasoning=True to capture LLM reasoning
            tasks.append(
                self.engine.play_round(
                    game_state, decision_makers_pair, capture_reasoning=True
                )
            )

        # Wait for all rounds to complete
        results = await asyncio.gather(*tasks)

        # Collect results
        for (p1_id, p2_id), result in zip(match_pairs, results):
            p1_decision = result.decisions.get(p1_id)
            p2_decision = result.decisions.get(p2_id)
            p1_payoff = result.payoffs.get(p1_id, 0)
            p2_payoff = result.payoffs.get(p2_id, 0)
            p1_reasoning = result.reasoning.get(p1_id, "")
            p2_reasoning = result.reasoning.get(p2_id, "")

            tournament_round.add_match_result(
                p1_id,
                p2_id,
                p1_decision,
                p2_decision,
                p1_payoff,
                p2_payoff,
                p1_reasoning,
                p2_reasoning,
            )

        return tournament_round

    def create_game_states(
        self, player_ids: list[str], rounds_per_match: int
    ) -> dict[tuple[str, str], GameState]:
        """Create GameState for each match pair."""
        game_states = {}

        for i, p1_id in enumerate(player_ids):
            for p2_id in player_ids[i + 1 :]:
                game_states[(p1_id, p2_id)] = GameState(
                    players=[
                        Player(p1_id, f"Player {p1_id}"),
                        Player(p2_id, f"Player {p2_id}"),
                    ],
                    rounds=[],
                    max_rounds=rounds_per_match,
                )

        return game_states

    async def play_match(
        self,
        player1: DecisionMaker,
        player2: DecisionMaker,
        player1_id: str,
        player2_id: str,
        player1_strategy: str,
        player2_strategy: str,
        rounds: int = 10,
    ) -> MatchResult:
        """
        Play a single match between two players (multiple rounds).

        Args:
            player1: Decision maker for player 1
            player2: Decision maker for player 2
            player1_id: ID for player 1
            player2_id: ID for player 2
            player1_strategy: Strategy name for player 1
            player2_strategy: Strategy name for player 2
            rounds: Number of rounds to play

        Returns:
            MatchResult with match details and history
        """
        game_state = GameState(
            players=[
                Player(player1_id, "Player 1"),
                Player(player2_id, "Player 2"),
            ],
            rounds=[],
            max_rounds=rounds,
        )

        decision_makers = [player1, player2]

        # Play all rounds
        round_history = []
        for _ in range(rounds):
            result = await self.engine.play_round(game_state, decision_makers)
            round_history.append(result)

        # Calculate totals
        player1_total = game_state.get_score(player1_id)
        player2_total = game_state.get_score(player2_id)

        # Determine winner
        if player1_total > player2_total:
            winner = "player1"
        elif player2_total > player1_total:
            winner = "player2"
        else:
            winner = "draw"

        match_result = MatchResult(
            player1_id=player1_id,
            player2_id=player2_id,
            player1_strategy=player1_strategy,
            player2_strategy=player2_strategy,
            player1_total_score=player1_total,
            player2_total_score=player2_total,
            rounds_played=rounds,
            round_history=round_history,
            winner=winner,
        )

        return match_result

    def create_tournament(
        self,
        player_ids: list[str],
        player_strategies: list[str],
        rounds_per_match: int = 10,
    ) -> TournamentState:
        """
        Initialize tournament state with all players.

        Args:
            player_ids: List of player IDs
            player_strategies: List of strategy names (same order as player_ids)
            rounds_per_match: Number of rounds per match

        Returns:
            TournamentState ready for matches
        """
        players = [Player(pid, f"Player {i + 1}") for i, pid in enumerate(player_ids)]

        return TournamentState(
            players=players,
            rounds_per_match=rounds_per_match,
            current_match_index=0,
        )

    def get_match_schedule(self, player_ids: list[str]) -> list[tuple[str, str]]:
        """
        Generate round-robin match schedule.

        Args:
            player_ids: List of player IDs

        Returns:
            List of (player1_id, player2_id) tuples for all matches
        """
        return list(itertools.combinations(player_ids, 2))

    async def run_full_tournament(
        self,
        decision_makers: dict[str, DecisionMaker],
        player_ids: list[str],
        player_strategies: list[str],
        rounds_per_match: int = 10,
    ) -> TournamentState:
        """
        Run a complete tournament with parallel rounds.

        In each round, ALL pairs play simultaneously. After all rounds,
        aggregate the results into match results.

        Args:
            decision_makers: Dict mapping player_id to DecisionMaker
            player_ids: List of all player IDs
            player_strategies: List of strategy names (same order as player_ids)
            rounds_per_match: Number of rounds per match

        Returns:
            TournamentState with all match results and tournament rounds
        """
        # Create strategy lookup
        strategy_map = dict(zip(player_ids, player_strategies))

        # Create tournament state
        tournament = self.create_tournament(
            player_ids, player_strategies, rounds_per_match
        )

        # Get all match pairings
        match_pairs = self.get_match_schedule(player_ids)

        # Create game states for each match pair
        game_states = self.create_game_states(player_ids, rounds_per_match)

        # Play each round - all matches in parallel
        for round_num in range(1, rounds_per_match + 1):
            tournament_round = await self.play_tournament_round(
                game_states=game_states,
                decision_makers=decision_makers,
                match_pairs=match_pairs,
                round_number=round_num,
            )
            tournament.add_tournament_round(tournament_round)

        # Aggregate results into match results
        for p1_id, p2_id in match_pairs:
            game_state = game_states[(p1_id, p2_id)]
            p1_strategy = strategy_map[p1_id]
            p2_strategy = strategy_map[p2_id]

            player1_total = game_state.get_score(p1_id)
            player2_total = game_state.get_score(p2_id)

            if player1_total > player2_total:
                winner = "player1"
            elif player2_total > player1_total:
                winner = "player2"
            else:
                winner = "draw"

            match_result = MatchResult(
                player1_id=p1_id,
                player2_id=p2_id,
                player1_strategy=p1_strategy,
                player2_strategy=p2_strategy,
                player1_total_score=player1_total,
                player2_total_score=player2_total,
                rounds_played=rounds_per_match,
                round_history=game_state.rounds,  # Contains all round results
                winner=winner,
            )

            tournament.add_match(match_result)
            tournament.current_match_index += 1

        return tournament
