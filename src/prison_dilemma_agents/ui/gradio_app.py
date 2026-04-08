import asyncio
import os
from pathlib import Path
from typing import Optional

import gradio as gr
import yaml

from prison_dilemma_agents.crew import PrisonDilemmaCrew
from prison_dilemma_agents.game.engine import GameEngine, Tournament
from prison_dilemma_agents.game.models import (
    Decision,
    GameState,
    Player,
    TournamentState,
)
from prison_dilemma_agents.game.simple_strategies import (
    AlwaysBetray,
    AlwaysCooperate,
    RandomDecisionMaker,
    SuspiciousTitForTat,
    TitForTat,
)
from prison_dilemma_agents.players.player import LLMPlayer, PlayerDecision


def _load_strategies_from_yaml() -> tuple[list[str], dict[str, str]]:
    """
    Load all strategies from agents.yaml file dynamically.

    Returns:
        - List of strategy display names for dropdown (players only, not game management)
        - Mapping of display name to agent key (ALL are LLM agents!)
    """
    # Find the config file - go up 2 levels from ui/gradio_app.py to prison_dilemma_agents/
    config_path = Path(__file__).parent.parent / "config" / "agents.yaml"

    if not config_path.exists():
        # Fallback to default strategies if config not found
        return _get_default_strategies()

    with open(config_path, "r") as f:
        agents_config = yaml.safe_load(f)

    strategies = []
    agent_mapping = {}  # ALL strategies are LLM agents from the crew

    # Display names with emojis for specific strategies
    emoji_map = {
        "always_cooperate": "🤝",
        "always_betray": "🦈",
        "random_player": "🎲",
        "tit_for_tat": "🪞",
        "tit_for_two_tats": "🕊️",
        "two_tits_for_tat": "⚔️",
        "grudger": "⚖️",
        "aggressive": "🐺",
        "adaptive": "🦎",
        "optimizer": "🧠",
        "probabilistic_cooperator": "🎰",
        "signaler": "📡",
        "llm_player_1": "🤖",
        "llm_player_2": "🤖",
    }

    # Only include PLAYER agents (those who actually play the game)
    # Exclude: game_manager, strategy_analyst, score_tracker, narrator
    player_agents = [
        "llm_player_1",
        "llm_player_2",
        "always_cooperate",
        "always_betray",
        "random_player",
        "tit_for_tat",
        "tit_for_two_tats",
        "two_tits_for_tat",
        "grudger",
        "aggressive",
        "adaptive",
        "optimizer",
        "probabilistic_cooperator",
        "signaler",
    ]

    for agent_key in player_agents:
        if agent_key not in agents_config:
            continue

        role = agents_config[agent_key].get("role", agent_key)

        # Map agent to its display name and key
        if "llm_player" in agent_key:
            player_num = agent_key.split("_")[-1].replace("player", "Player ")
            display_name = f"🤖 LLM: {player_num}"
        else:
            # Extract clean name from role (e.g., "Always Cooperate Player" -> "Always Cooperate")
            clean_name = role.replace("Player", "").strip()
            emoji = emoji_map.get(agent_key, "🎯")
            display_name = f"{emoji} {clean_name}"

        strategies.append(display_name)
        agent_mapping[display_name] = agent_key

    return strategies, agent_mapping


def _get_default_strategies() -> tuple[list[str], dict[str, str]]:
    """Fallback default strategies if YAML not found."""
    strategies = [
        "🤖 LLM: Tit for Tat",
        "🤖 LLM: Aggressive",
        "🤖 LLM: Adaptive",
        "🤖 LLM: Optimizer",
        "🤝 Always Cooperate",
        "🦈 Always Betray",
        "🎲 Random",
        "🪞 Tit for Tat",
        "🕊️ TFT Two Tats",
    ]
    llm_mapping = {
        "🤖 LLM: Tit for Tat": "tit_for_tat",
        "🤖 LLM: Aggressive": "aggressive",
        "🤖 LLM: Adaptive": "adaptive",
        "🤖 LLM: Optimizer": "optimizer",
    }
    return strategies, llm_mapping


# Load strategies dynamically from YAML
# All strategies in agents.yaml are LLM agents from the crew
AVAILABLE_STRATEGIES, LLM_AGENT_MAPPING = _load_strategies_from_yaml()

# All strategies are LLM agents - no simple bots needed!
SIMPLE_BOTS = {}

# Use dynamically loaded strategies from YAML
ALL_STRATEGIES = AVAILABLE_STRATEGIES

# Display names with emojis
STRATEGY_DISPLAY = {
    "llm_tit_for_tat": "🤖 LLM: Tit for Tat",
    "llm_aggressive": "🤖 LLM: Aggressive",
    "llm_adaptive": "🤖 LLM: Adaptive",
    "llm_optimizer": "🤖 LLM: Optimizer",
    "always_cooperate": "🤝 Always Cooperate",
    "always_betray": "🦈 Always Betray",
    "random": "🎲 Random",
    "tit_for_tat": "🪞 Tit for Tat",
    "tit_for_two_tats": "🕊️ TFT Two Tats",
    "two_tits_for_tat": "⚔️ Two Tits for Tat",
    "grudger": "⚖️ Grudger",
    "aggressive": "🐺 Aggressive",
    "adaptive": "🦎 Adaptive",
    "optimizer": "🧠 Optimizer",
    "probabilistic_cooperator": "🎰 Probabilistic",
    "signaler": "📡 Signaler",
}


def get_display_name(strategy_key: str) -> str:
    """Get display name with emoji for a strategy."""
    key = (
        strategy_key.lower().replace("🤖 ", "llm_").replace(" ", "_").replace(":", "_")
    )
    return STRATEGY_DISPLAY.get(key, strategy_key)


def _is_llm_strategy(strategy: str) -> bool:
    """Check if a strategy uses an LLM agent."""
    # All strategies from YAML are LLM agents from the crew!
    return strategy in LLM_AGENT_MAPPING


def _get_llm_agent_config(strategy: str) -> str:
    """Map LLM strategy to agent config key."""
    # Use dynamically loaded mapping from YAML
    return LLM_AGENT_MAPPING.get(strategy, "llm_player_1")


async def run_game(
    player1_strategy: str,
    player2_strategy: str,
    num_rounds: int,
) -> tuple[str, str, str]:
    """
    Run a complete game and return results.

    Uses LLM narrators and optional LLM players.
    """
    # Create crew instance
    crew_instance = PrisonDilemmaCrew()

    # Create game state
    game_state = GameState(
        players=[Player("p1", "Player 1"), Player("p2", "Player 2")],
        rounds=[],
        max_rounds=num_rounds,
    )

    # Create decision makers
    decision_makers = []

    # Player 1
    if _is_llm_strategy(player1_strategy):
        agent_key = _get_llm_agent_config(player1_strategy)
        # Get agent by method name from crew instance
        agent = getattr(crew_instance, agent_key, None)()
        if agent:
            decision_makers.append(LLMPlayer("p1", agent, name="Player 1"))
        else:
            decision_makers.append(TitForTat())
    else:
        if player1_strategy in SIMPLE_BOTS:
            decision_makers.append(SIMPLE_BOTS[player1_strategy]())
        else:
            decision_makers.append(TitForTat())

    # Player 2
    if _is_llm_strategy(player2_strategy):
        agent_key = _get_llm_agent_config(player2_strategy)
        agent = getattr(crew_instance, agent_key, None)()
        if agent:
            decision_makers.append(LLMPlayer("p2", agent, name="Player 2"))
        else:
            decision_makers.append(AlwaysBetray())
        if agent:
            decision_makers.append(LLMPlayer("p2", agent, name="Player 2"))
        else:
            decision_makers.append(AlwaysBetray())
    else:
        if player2_strategy in SIMPLE_BOTS:
            decision_makers.append(SIMPLE_BOTS[player2_strategy]())
        else:
            decision_makers.append(AlwaysBetray())

    # Create engine
    engine = GameEngine()

    # Get narrator agent
    narrator_agent = getattr(crew_instance, "narrator", None)()

    # Run rounds
    results = []
    for i in range(num_rounds):
        result = await engine.play_round(game_state, decision_makers)

        # Get player reasoning
        p1_reasoning = await _get_player_reasoning(
            decision_makers[0], game_state, result.decisions["p1"], "Player 1"
        )
        p2_reasoning = await _get_player_reasoning(
            decision_makers[1], game_state, result.decisions["p2"], "Player 2"
        )

        round_data = {
            "round": i + 1,
            "p1_decision": result.decisions["p1"],
            "p2_decision": result.decisions["p2"],
            "p1_payoff": result.payoffs["p1"],
            "p2_payoff": result.payoffs["p2"],
            "p1_reasoning": p1_reasoning,
            "p2_reasoning": p2_reasoning,
        }
        results.append(round_data)

    # Generate narrator commentary (using LLM!)
    narrator = await _generate_llm_narrator(
        narrator_agent, results, game_state, player1_strategy, player2_strategy
    )

    # Generate final summary
    final_summary = _generate_final_summary(
        results, game_state, player1_strategy, player2_strategy
    )

    # Generate round history
    round_history = _generate_round_history(results)

    return round_history, narrator, final_summary


async def run_tournament(
    selected_strategies: list[str],
    rounds_per_match: int,
) -> tuple[str, str, str]:
    """
    Run a tournament where each strategy plays against all others.

    Args:
        selected_strategies: List of strategies to include in tournament
        rounds_per_match: Number of rounds per match

    Returns:
        Tuple of (leaderboard, match_details, round_history)
    """
    if len(selected_strategies) < 2:
        return "# ❌ Need at least 2 players for a tournament!", "", ""

    # Create crew instance
    crew_instance = PrisonDilemmaCrew()

    # Create tournament engine
    tournament_engine = Tournament()

    # Prepare decision makers for each player
    decision_makers = {}
    player_ids = []
    player_strategies = []

    for i, strategy in enumerate(selected_strategies):
        player_id = f"player_{i}"
        player_ids.append(player_id)
        player_strategies.append(strategy)

        # Create appropriate decision maker
        if _is_llm_strategy(strategy):
            agent_key = _get_llm_agent_config(strategy)
            agent = getattr(crew_instance, agent_key, None)()
            if agent:
                decision_makers[player_id] = LLMPlayer(
                    player_id, agent, name=f"Player {i + 1}"
                )
            else:
                decision_makers[player_id] = TitForTat()
        else:
            # Map to simple bot
            strategy_key = (
                strategy.lower()
                .replace(" ", "_")
                .replace("🤝", "")
                .replace("🦈", "")
                .replace("🎲", "")
                .replace("🪞", "")
                .replace("🕊️", "")
                .replace("⚔️", "")
                .replace("⚖️", "")
                .replace("🐺", "")
                .replace("🦎", "")
                .replace("🧠", "")
                .replace("🎰", "")
                .replace("📡", "")
                .strip()
            )
            if "always_cooperate" in strategy_key:
                decision_makers[player_id] = AlwaysCooperate()
            elif "always_betray" in strategy_key:
                decision_makers[player_id] = AlwaysBetray()
            elif "random" in strategy_key:
                decision_makers[player_id] = RandomDecisionMaker()
            else:
                decision_makers[player_id] = TitForTat()

    # Run the tournament
    tournament_state = await tournament_engine.run_full_tournament(
        decision_makers=decision_makers,
        player_ids=player_ids,
        player_strategies=player_strategies,
        rounds_per_match=rounds_per_match,
    )

    # Generate leaderboard
    leaderboard = _generate_tournament_leaderboard(
        tournament_state, selected_strategies
    )

    # Generate match details
    match_details = _generate_tournament_details(tournament_state, selected_strategies)

    # Generate round history
    round_history = _generate_tournament_round_history(
        tournament_state, selected_strategies
    )

    return leaderboard, match_details, round_history


def _generate_tournament_leaderboard(
    tournament_state: TournamentState, strategies: list[str]
) -> str:
    """Generate tournament leaderboard showing final standings."""
    lines = ["# 🏆 Tournament Leaderboard", ""]

    # Build scores
    scores = []
    for i, strategy in enumerate(strategies):
        player_id = f"player_{i}"
        total_score = tournament_state.get_player_score(player_id)
        total_rounds = tournament_state.get_player_total_rounds(player_id)
        matches_played = sum(
            1
            for m in tournament_state.matches
            if m.player1_id == player_id or m.player2_id == player_id
        )

        emoji = "🤖" if _is_llm_strategy(strategy) else "🎯"
        display_name = (
            get_display_name(strategy) if not _is_llm_strategy(strategy) else strategy
        )

        scores.append(
            {
                "strategy": strategy,
                "display": f"{emoji} {display_name}",
                "score": total_score,
                "rounds": total_rounds,
                "matches": matches_played,
            }
        )

    # Sort by score descending
    scores.sort(key=lambda x: x["score"], reverse=True)

    # Add header
    lines.append("| Rank | Strategy | Total Coins | Matches | Rounds Played |")
    lines.append("|------|----------|-------------|---------|---------------|")

    for i, s in enumerate(scores):
        rank_emoji = (
            "🥇" if i == 0 else ("🥈" if i == 1 else ("🥉" if i == 2 else "  "))
        )
        lines.append(
            f"| {rank_emoji} | {s['display']} | **{s['score']}** | {s['matches']} | {s['rounds']} |"
        )

    lines.append("")

    # Determine winner
    winners = tournament_state.get_winner()
    if len(winners) == 1:
        winner_idx = int(winners[0].split("_")[1])
        winner_strategy = strategies[winner_idx]
        winner_name = (
            get_display_name(winner_strategy)
            if not _is_llm_strategy(winner_strategy)
            else winner_strategy
        )
        lines.append(f"## 🏅 Winner: **{winner_name}**")
    else:
        lines.append("## 🤝 It's a tie!")
        for w in winners:
            idx = int(w.split("_")[1])
            lines.append(f"- {get_display_name(strategies[idx])}")

    return "\n".join(lines)


def _generate_tournament_details(
    tournament_state: TournamentState, strategies: list[str]
) -> str:
    """
    Generate detailed match results organized by rounds.
    Each round shows all matches happening in that round as separate tables.
    """
    lines = ["# 📊 Match Details", ""]

    # Get rounds per match
    rounds_per_match = (
        tournament_state.matches[0].rounds_played if tournament_state.matches else 0
    )

    # Organize matches by their round number
    # Each match has multiple rounds, we'll show them grouped

    for round_num in range(1, rounds_per_match + 1):
        lines.append(f"## 🎯 Round {round_num}")
        lines.append("")

        # Show each match's results for this round
        match_tables = []
        for match_idx, match in enumerate(tournament_state.matches):
            if round_num <= len(match.round_history):
                round_result = match.round_history[round_num - 1]

                p1_idx = int(match.player1_id.split("_")[1])
                p2_idx = int(match.player2_id.split("_")[1])

                p1_strategy = strategies[p1_idx]
                p2_strategy = strategies[p2_idx]

                p1_display = (
                    get_display_name(p1_strategy)
                    if not _is_llm_strategy(p1_strategy)
                    else p1_strategy
                )
                p2_display = (
                    get_display_name(p2_strategy)
                    if not _is_llm_strategy(p2_strategy)
                    else p2_strategy
                )

                p1_decision = round_result.decisions.get(match.player1_id)
                p2_decision = round_result.decisions.get(match.player2_id)
                p1_payoff = round_result.payoffs.get(match.player1_id, 0)
                p2_payoff = round_result.payoffs.get(match.player2_id, 0)
                p1_reasoning = round_result.reasoning.get(match.player1_id, "")
                p2_reasoning = round_result.reasoning.get(match.player2_id, "")

                p1_emoji = "🤝" if p1_decision == Decision.COOPERATE else "💢"
                p2_emoji = "🤝" if p2_decision == Decision.COOPERATE else "💢"

                # Create a mini table for this match including reasoning
                if p1_reasoning or p2_reasoning:
                    # Show reasoning in separate rows
                    table = f"| **{p1_display}** | {p1_emoji} {p1_decision.value if p1_decision else '-'} | +{p1_payoff} | _{p1_reasoning}_ |"
                    table += f"\n| **{p2_display}** | {p2_emoji} {p2_decision.value if p2_decision else '-'} | +{p2_payoff} | _{p2_reasoning}_ |"
                else:
                    table = f"| **{p1_display}** | {p1_emoji} {p1_decision.value if p1_decision else '-'} | +{p1_payoff} |"
                    table += f"\n| **{p2_display}** | {p2_emoji} {p2_decision.value if p2_decision else '-'} | +{p2_payoff} |"

                match_tables.append(
                    (
                        f"{p1_display} vs {p2_display}",
                        table,
                        p1_reasoning or p2_reasoning,
                    )
                )

        # Display tables in a row (using inline tables or multiple columns)
        # Gradio markdown supports multiple tables - we'll show them as separate blocks
        for match_name, table, has_reasoning in match_tables:
            lines.append(f"**{match_name}**")
            if has_reasoning:
                lines.append("| Player | Decision | Points | Reasoning |")
                lines.append("|--------|----------|--------|-----------|")
            else:
                lines.append("| Player | Decision | Points |")
                lines.append("|--------|----------|--------|")
            lines.append(table)
            lines.append("")

        lines.append("---")
        lines.append("")

    # Add cumulative scores after all rounds
    lines.append("## 📈 Cumulative Scores (End of Tournament)")
    lines.append("")
    lines.append("| Player | Total Score |")
    lines.append("|--------|-------------|")

    # Get final scores per player
    for i, strategy in enumerate(strategies):
        player_id = f"player_{i}"
        total_score = tournament_state.get_player_score(player_id)

        display_name = (
            get_display_name(strategy) if not _is_llm_strategy(strategy) else strategy
        )

        lines.append(f"| {display_name} | **{total_score}** |")

    return "\n".join(lines)


def _generate_tournament_round_history(
    tournament_state: TournamentState, strategies: list[str]
) -> str:
    """Generate round-by-round history for all matches in the tournament."""
    lines = ["# 🎮 Tournament Round History", ""]

    for match_idx, match in enumerate(tournament_state.matches):
        p1_idx = int(match.player1_id.split("_")[1])
        p2_idx = int(match.player2_id.split("_")[1])

        p1_strategy = strategies[p1_idx]
        p2_strategy = strategies[p2_idx]

        p1_display = (
            get_display_name(p1_strategy)
            if not _is_llm_strategy(p1_strategy)
            else p1_strategy
        )
        p2_display = (
            get_display_name(p2_strategy)
            if not _is_llm_strategy(p2_strategy)
            else p2_strategy
        )

        lines.append(f"## Match {match_idx + 1}: {p1_display} vs {p2_display}")
        lines.append("")

        if not match.round_history:
            lines.append("*No rounds played*")
            lines.append("")
            continue

        # Round-by-round breakdown
        for round_idx, round_result in enumerate(match.round_history):
            p1_decision = round_result.decisions.get(match.player1_id)
            p2_decision = round_result.decisions.get(match.player2_id)
            p1_payoff = round_result.payoffs.get(match.player1_id, 0)
            p2_payoff = round_result.payoffs.get(match.player2_id, 0)

            p1_emoji = "🤝" if p1_decision == Decision.COOPERATE else "💢"
            p2_emoji = "🤝" if p2_decision == Decision.COOPERATE else "💢"

            # Determine round outcome
            if p1_decision == p2_decision:
                outcome = (
                    "🤝 Mutual Cooperate"
                    if p1_decision == Decision.COOPERATE
                    else "💀 Mutual Defect"
                )
            elif p1_decision == Decision.BETRAY:
                outcome = "💥 P1 exploits P2"
            else:
                outcome = "💥 P2 exploits P1"

            lines.append(f"### Round {round_idx + 1} - {outcome}")
            lines.append("")
            lines.append("| | Decision | Points |")
            lines.append("|---|---|---|")
            lines.append(
                f"| 🤿 {p1_display} | {p1_emoji} {p1_decision.value if p1_decision else '?'} | +{p1_payoff} |"
            )
            lines.append(
                f"| 🐙 {p2_display} | {p2_emoji} {p2_decision.value if p2_decision else '?'} | +{p2_payoff} |"
            )
            lines.append("")

        # Match summary
        lines.append(
            f"**Match Score:** 🤿 {match.player1_total_score} - {match.player2_total_score} 🐙"
        )

        if match.winner == "player1":
            lines.append(f"Winner: **{p1_display}**")
        elif match.winner == "player2":
            lines.append(f"Winner: **{p2_display}**")
        else:
            lines.append("Result: **Draw**")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


async def _get_player_reasoning(
    decision_maker, game_state: GameState, decision: Decision, player_name: str
) -> str:
    """Get reasoning from player (LLM or generate)."""
    if isinstance(decision_maker, LLMPlayer):
        # For LLM players, ask them to explain
        prompt = f"""You just made a decision in the Prisoner's Dilemma.

Your decision: {decision.value}

Give a Brief 1-2 sentence explanation of WHY you made this choice.
Be concise and conversational, as if you're thinking out loud.
"""
        try:
            result = await decision_maker.agent.kickoff_async(
                prompt,
                response_format=PlayerDecision,
            )
            return result.pydantic.reasoning
        except Exception:
            return "Strategic decision made."
    else:
        # For simple bots, generate explanation based on strategy
        return _generate_simple_reasoning(decision, game_state, player_name)


def _generate_simple_reasoning(
    decision: Decision, game_state: GameState, player_name: str
) -> str:
    """Generate reasoning for simple bot."""
    if not game_state.rounds:
        if decision == Decision.COOPERATE:
            return "Starting with trust. Let's see how this goes."
        else:
            return "Going aggressive from the start. Watch out!"

    opponent_id = "p2" if player_name == "Player 1" else "p1"
    opponent_move = game_state.get_opponent_last_move(opponent_id)

    if decision == Decision.COOPERATE:
        if opponent_move == Decision.COOPERATE:
            return "They trusted me, so I trust them back. Building rapport."
        else:
            return "I choose to forgive. Maybe it was a mistake. Trust restored."
    else:
        if opponent_move == Decision.BETRAY:
            return "They betrayed me. Now they get a taste of their own medicine."
        else:
            return "Exploiting the opportunity. Can't pass up these gains!"


async def _generate_llm_narrator(
    narrator_agent,
    results: list,
    game_state: GameState,
    p1_strategy: str,
    p2_strategy: str,
) -> str:
    """Generate narrator commentary using LLM."""
    if not narrator_agent:
        return _generate_fallback_narrator(results, game_state)

    # Build context
    p1_score = game_state.get_score("p1")
    p2_score = game_state.get_score("p2")

    summary = []
    for r in results:
        p1_emoji = "🤝" if r["p1_decision"] == Decision.COOPERATE else "💢"
        p2_emoji = "🤝" if r["p2_decision"] == Decision.COOPERATE else "💢"
        summary.append(f"Round {r['round']}: P1={p1_emoji}, P2={p2_emoji}")

    prompt = f"""You are a dramatic sports commentator for a Prisoner's Dilemma game.

GAME SUMMARY:
- Player 1 ({get_display_name(p1_strategy)}): {p1_score} points
- Player 2 ({get_display_name(p2_strategy)}): {p2_score} points
- Rounds played: {len(results)}

ROUND BY ROUND:
{chr(10).join(summary)}

Create 3-4 dramatic commentary sections:
1. An opening statement about the matchup
2. Highlights from key moments (betrayals, cooperation, turning points)
3. A final verdict announcing the winner

Be entertaining, dramatic, and use sports commentator style.
Keep it engaging but not too long (under 300 words total).
Use emojis for dramatic effect.
"""

    try:
        result = await narrator_agent.kickoff_async(prompt)
        return f"# 📺 Narrator's Commentary\n\n{result.raw}"
    except Exception as e:
        return (
            f"# 📺 Narrator's Commentary\n\n*(LLM unavailable: {e})*\n\n"
            + _generate_fallback_narrator(results, game_state)
        )


def _generate_fallback_narrator(results: list, game_state: GameState) -> str:
    """Generate fallback narrator commentary without LLM."""
    if not results:
        return ""

    commentary = ["# 📺 Narrator's Commentary", ""]
    commentary.append(
        "🎬 **Welcome to the Prisoner's Dilemma!** "
        "Two strategies enter, only one leaves victorious!"
    )
    commentary.append("")

    betrayals = sum(
        1
        for r in results
        if r["p1_decision"] == Decision.BETRAY or r["p2_decision"] == Decision.BETRAY
    )
    cooperations = len(results) * 2 - betrayals
    commentary.append(f"📊 **The Stats:** {cooperations} 🤝, {betrayals} 💢")
    commentary.append("")

    for i, r in enumerate(results):
        if (
            r["p1_decision"] == Decision.BETRAY
            and r["p2_decision"] == Decision.COOPERATE
        ):
            commentary.append(
                f"💥 **Round {i + 1}:** Player 1 exploits Player 2's trust!"
            )
        elif (
            r["p2_decision"] == Decision.BETRAY
            and r["p1_decision"] == Decision.COOPERATE
        ):
            commentary.append(
                f"💥 **Round {i + 1}:** Player 2 strikes! The betrayal stings!"
            )
        elif (
            r["p1_decision"] == Decision.BETRAY and r["p2_decision"] == Decision.BETRAY
        ):
            commentary.append(
                f"🧊 **Round {i + 1}:** Mutual betrayal! Neither trusts the other..."
            )
        elif i < 3:
            commentary.append(f"🤝 **Round {i + 1}:** Beautiful mutual cooperation!")

    commentary.append("")
    p1_score = game_state.get_score("p1")
    p2_score = game_state.get_score("p2")

    if p1_score > p2_score:
        commentary.append(
            f"🏆 **Winner: Player 1!** Final: {p1_score} - {p2_score}. Dominant!"
        )
    elif p2_score > p1_score:
        commentary.append(
            f"🏆 **Winner: Player 2!** Final: {p2_score} - {p1_score}. Masterful!"
        )
    else:
        commentary.append(f"🤝 **It's a draw!** Both with {p1_score} points. Balanced!")

    return "\n".join(commentary)


def _generate_final_summary(
    results: list, game_state: GameState, p1_strategy: str, p2_strategy: str
) -> str:
    """Generate final game summary."""
    p1_score = game_state.get_score("p1")
    p2_score = game_state.get_score("p2")

    p1_coop = sum(1 for r in results if r["p1_decision"] == Decision.COOPERATE)
    p2_coop = sum(1 for r in results if r["p2_decision"] == Decision.COOPERATE)

    winner = (
        "Player 1"
        if p1_score > p2_score
        else ("Player 2" if p2_score > p1_score else "Draw")
    )

    verdict = (
        "Player 1 dominated!"
        if p1_score > p2_score
        else (
            "Player 2 showed superior strategy!"
            if p2_score > p1_score
            else "A perfectly balanced match!"
        )
    )

    return f"""
# 🏆 Game Over!

## Final Result

| | Player 1 | Player 2 |
|---|---|---|
| **Strategy** | {get_display_name(p1_strategy)} | {get_display_name(p2_strategy)} |
| **Final Score** | **{p1_score}** | **{p2_score}** |
| **Cooperations** | {p1_coop}/{len(results)} | {p2_coop}/{len(results)} |

## 🏅 Winner: **{winner}**

{verdict}
"""


def _generate_round_history(results: list) -> str:
    """Generate round-by-round history markdown."""
    if not results:
        return "No rounds played yet."

    lines = ["# 🎮 Round History", ""]

    for r in results:
        p1_emoji = "🤝" if r["p1_decision"] == Decision.COOPERATE else "💢"
        p2_emoji = "🤝" if r["p2_decision"] == Decision.COOPERATE else "💢"

        if r["p1_decision"] == r["p2_decision"]:
            outcome = (
                "🤝 Mutual"
                if r["p1_decision"] == Decision.COOPERATE
                else "💀 Mutual Defection"
            )
        elif r["p1_decision"] == Decision.BETRAY:
            outcome = "💥 P1 exploits P2"
        else:
            outcome = "💥 P2 exploits P1"

        lines.append(f"## Round {r['round']} - {outcome}")
        lines.append("")
        lines.append("| | Decision | Reasoning |")
        lines.append("|---|---|---|")
        lines.append(
            f"| 🤿 P1 | {p1_emoji} {r['p1_decision'].value} | {r['p1_reasoning']} |"
        )
        lines.append(
            f"| 🐙 P2 | {p2_emoji} {r['p2_decision'].value} | {r['p2_reasoning']} |"
        )
        lines.append("")
        lines.append(f"**Points:** 🤿 +{r['p1_payoff']} | 🐙 +{r['p2_payoff']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def create_ui():
    """Create and return the Gradio UI."""
    with gr.Blocks(
        title="🎮 Prisoner's Dilemma",
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="purple"),
    ) as demo:
        gr.Markdown("""
        # 🎮 Prisoner's Dilemma Arena

        *Where trust meets betrayal, and strategies clash!*

        🤖 = LLM-powered player (uses AI Agents to make decisions)
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## ⚙️ Game Setup")

                player1 = gr.Dropdown(
                    choices=ALL_STRATEGIES,
                    value="🪞 Tit for Tat",
                    label="🤿 Player 1",
                    info="Choose Player 1's strategy",
                )

                player2 = gr.Dropdown(
                    choices=ALL_STRATEGIES,
                    value="🤖 LLM: 2",
                    label="🐙 Player 2",
                    info="Choose Player 2's strategy",
                )

                rounds = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="🎯 Rounds",
                    info="Game length (fewer rounds = faster with LLM)",
                )

                run_btn = gr.Button("🚀 Play Game", variant="primary", size="lg")

                gr.Markdown("""
                **Note:** LLM players take longer but provide better reasoning.
                """)

            with gr.Column(scale=2):
                gr.Markdown("## 📊 Game Results")

                with gr.Tab("🎮 Round History"):
                    round_history = gr.Markdown("*Select strategies and click Play*")

                with gr.Tab("📺 Commentary"):
                    narrator_output = gr.Markdown(
                        "*Narrator will comment on the action...*"
                    )

                with gr.Tab("🏆 Final"):
                    final_result = gr.Markdown("*Awaiting game completion*")

        run_btn.click(
            fn=run_game,
            inputs=[player1, player2, rounds],
            outputs=[round_history, narrator_output, final_result],
        )

        gr.Markdown("""
        ---
        ## 🏆 Tournament Mode
        
        *All players compete against each other! Winner takes all.*
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Tournament Setup")

                tournament_players = gr.CheckboxGroup(
                    choices=ALL_STRATEGIES,
                    value=["🪞 Tit for Tat", "🤝 Always Cooperate", "🦈 Always Betray"],
                    label="🏅 Select Players",
                    info="Choose at least 2 strategies",
                )

                tournament_rounds = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="🎯 Rounds",
                    info="Each match consists of this many rounds",
                )

                run_tournament_btn = gr.Button(
                    "🚀 Start Tournament", variant="primary", size="lg"
                )

                gr.Markdown("""
                **Tournament Rules:**
                - Each player plays against every other player
                - Total matches = n × (n-1) where n = number of players
                - Winner is who collects the most coins across all matches
                """)

            with gr.Column(scale=2):
                gr.Markdown("### 📊 Tournament Results")

                with gr.Tab("🏅 Leaderboard"):
                    tournament_leaderboard = gr.Markdown(
                        "*Select players and start tournament*"
                    )

                with gr.Tab("📋 Match Details"):
                    tournament_details = gr.Markdown("*Match results will appear here*")

                with gr.Tab("🎮 Round History"):
                    tournament_round_history = gr.Markdown(
                        "*Round-by-round details will appear here*"
                    )

        run_tournament_btn.click(
            fn=run_tournament,
            inputs=[tournament_players, tournament_rounds],
            outputs=[
                tournament_leaderboard,
                tournament_details,
                tournament_round_history,
            ],
        )

        gr.Markdown("""
        ---
        ### 📖 Strategies

        | Strategy | Description |
        |---|---|
        | 🤝 Always Cooperate | Trusts blindly, never defects |
        | 💢 Always Betray | Exploits everyone, never trusts |
        | 🎲 Random | Pure chaos, 50/50 |
        | 🪞 Tit for Tat | Mirrors opponent's last move |
        | 🤖 LLM: Aggressive | AI player with aggressive strategy |
        | 🤖 LLM: Adaptive | AI player that adapts to opponent |

        ### 🏆 Payoff Matrix

        | | Opp Cooperates | Opp Defects |
        |---|---|---|
        | **You Cooperate** | 3, 3 | 0, 5 |
        | **You Defect** | 5, 0 | 1, 1 |
        """)

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch()
