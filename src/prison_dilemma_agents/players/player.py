"""
LLM-powered Player Agent for Prisoner's Dilemma.

This module provides the LLMPlayer class that wraps a CrewAI agent
and implements the DecisionMaker protocol for the game engine.
"""

from typing import Optional

from pydantic import BaseModel

from prison_dilemma_agents.game.engine import DecisionMaker
from prison_dilemma_agents.game.models import Decision, GameState


class PlayerDecision(BaseModel):
    """Structured output from LLM decision-making."""

    decision: Decision
    reasoning: str


class LLMPlayer(DecisionMaker):
    """
    LLM-powered decision maker that implements DecisionMaker protocol.

    Wraps a CrewAI Agent to make strategic decisions using AI.
    Strategy is defined in YAML (backstory/goal), this just provides game state.
    """

    def __init__(
        self,
        player_id: str,
        agent,
        name: str = "",
    ):
        """
        Initialize an LLM player.

        Args:
            player_id: Unique identifier for this player
            agent: CrewAI Agent instance (strategy defined in YAML)
            name: Display name for the player
        """
        self.player_id = player_id
        self.agent = agent
        self.name = name or player_id
        self.last_reasoning = ""  # Store reasoning from last decision

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        """
        Make a decision using the LLM agent.

        Strategy/personality is defined in YAML. This just provides game state.

        Args:
            game_state: Current game state including history
            player_id: ID of the player (unused, kept for protocol)

        Returns:
            Decision.COOPERATE or Decision.BETRAY
        """
        prompt = self._build_prompt(game_state)
        result = await self.agent.kickoff_async(
            prompt,
            response_format=PlayerDecision,
        )
        # Store reasoning for later use
        self.last_reasoning = result.pydantic.reasoning
        return result.pydantic.decision

    def get_reasoning(self) -> str:
        """Get the reasoning from the last decision."""
        return self.last_reasoning

    def _build_prompt(self, game_state: GameState) -> str:
        """Build a minimal prompt with game state data."""
        opponent_last_move = game_state.get_opponent_last_move(self.player_id)
        history = self._format_history(game_state)

        return f"""Score: {game_state.get_score(self.player_id)}
Opp last move: {opponent_last_move.value if opponent_last_move else "None"}
Remaining: {game_state.get_rounds_remaining()}/{game_state.max_rounds}

History:
{history}

Decide: COOPERATE or BETRAY."""

    def _format_history(self, game_state: GameState) -> str:
        """Format game history for the prompt."""
        if not game_state.rounds:
            return "No history yet."

        lines = []
        for i, round_result in enumerate(game_state.rounds, 1):
            my_move = round_result.decisions.get(self.player_id)
            opponent_id = game_state.get_opponent_id(self.player_id)
            opponent_move = round_result.decisions.get(opponent_id)
            lines.append(
                f"Round {i}: You={my_move.value if my_move else '?'}, Opp={opponent_move.value if opponent_move else '?'}"
            )

        return "\n".join(lines)


class HumanPlayer(DecisionMaker):
    """
    Human-controlled player for interactive games.

    Waits for human input via a callback function.
    """

    def __init__(
        self,
        player_id: str,
        name: str = "",
        input_callback=None,
    ):
        """
        Initialize a human player.

        Args:
            player_id: Unique identifier for this player
            name: Display name for the player
            input_callback: Async function to get human input -> Decision
        """
        self.player_id = player_id
        self.name = name or player_id
        self.input_callback = input_callback

    async def decide(self, game_state: GameState, player_id: str) -> Decision:
        """
        Get decision from human input.

        Args:
            game_state: Current game state (for display)
            player_id: ID of the player

        Returns:
            Decision.COOPERATE or Decision.BETRAY from human input
        """
        if self.input_callback:
            return await self.input_callback(game_state, self)

        raise NotImplementedError(
            "HumanPlayer requires an input_callback to get human decisions."
        )
