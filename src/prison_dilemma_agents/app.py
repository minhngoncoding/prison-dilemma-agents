"""
Prisoner's Dilemma Game UI with 3 AI Agents
Uses Gradio for the interface
"""

import gradio as gr
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class Choice(str, Enum):
    COOPERATE = "Cooperate"
    BETRAY = "Betray"


@dataclass
class AgentState:
    name: str
    backstory: str
    choice: Optional[Choice] = None
    reasoning: str = ""
    total_score: int = 0


PAYPFF_MATRIX = {
    (Choice.COOPERATE, Choice.COOPERATE, Choice.COOPERATE): (4, 4, 4),
    (Choice.COOPERATE, Choice.COOPERATE, Choice.BETRAY): (1, 1, 5),
    (Choice.COOPERATE, Choice.BETRAY, Choice.COOPERATE): (1, 5, 1),
    (Choice.COOPERATE, Choice.BETRAY, Choice.BETRAY): (0, 3, 3),
    (Choice.BETRAY, Choice.COOPERATE, Choice.COOPERATE): (5, 1, 1),
    (Choice.BETRAY, Choice.COOPERATE, Choice.BETRAY): (3, 0, 3),
    (Choice.BETRAY, Choice.BETRAY, Choice.COOPERATE): (3, 3, 0),
    (Choice.BETRAY, Choice.BETRAY, Choice.BETRAY): (2, 2, 2),
}


def create_agents():
    return [
        AgentState(
            name="Alice",
            backstory="Alice believes in the power of trust and cooperation. She values long-term relationships and thinks betraying others will come back to haunt you.",
        ),
        AgentState(
            name="Bob",
            backstory="Bob is a rational strategist who always looks out for himself. He believes in game theory and knows that betrayal often yields better individual outcomes.",
        ),
        AgentState(
            name="Charlie",
            backstory="Charlie is cautious and adaptive. He starts with trust but adjusts his strategy based on how others treat him. He believes in reciprocity.",
        ),
    ]


def calculate_round_payoffs(
    choices: tuple[Choice, Choice, Choice],
) -> tuple[int, int, int]:
    return PAYPFF_MATRIX[choices]


def get_agent_reasoning(
    agent: AgentState, others_choices: list[tuple[str, Choice]], history: list[dict]
) -> str:
    if agent.name == "Alice":
        return "Alice chooses to COOPERATE because she believes in the power of trust. In an iterated game, cooperation builds lasting relationships that benefit everyone in the long run."

    elif agent.name == "Bob":
        return "Bob chooses to BETRAY because it's the dominant strategy in a one-shot game. Even in iterated games, he calculates that short-term gains from betrayal outweigh potential future losses from retaliation."

    elif agent.name == "Charlie":
        if not history:
            return "Charlie chooses to COOPERATE initially. He'll observe the others' behavior and respond accordingly, believing in tit-for-tat with forgiveness."
        last_round = history[-1]
        alice_last = last_round.get("Alice", Choice.COOPERATE)
        bob_last = last_round.get("Bob", Choice.BETRAY)
        if alice_last == Choice.BETRAY or bob_last == Choice.BETRAY:
            return "Charlie notices betrayal from others and decides to BETRAY as a protective measure. He believes in reciprocity - you get what you give."
        return "Charlie sees cooperation from others and chooses to COOPERATE as well, maintaining the cycle of trust and goodwill."


def get_agent_choice(agent: AgentState, round_num: int) -> Choice:
    if agent.name == "Alice":
        return Choice.COOPERATE
    elif agent.name == "Bob":
        return Choice.BETRAY
    else:
        if round_num == 1:
            return Choice.COOPERATE
        return Choice.COOPERATE


class PrisonDilemmaGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.agents = create_agents()
        self.round = 0
        self.history: list[dict] = []
        self.game_log = ""

    def play_round(self):
        choices = []
        reasoning_lines = []

        for i, agent in enumerate(self.agents):
            others_history = [
                (self.agents[j].name, self.agents[j].choice)
                for j in range(len(self.agents))
                if j != i
            ]
            agent.choice = get_agent_choice(agent, self.round + 1)
            agent.reasoning = get_agent_reasoning(agent, others_history, self.history)
            choices.append(agent.choice)

            reasoning_lines.append(f"**{agent.name}** ({agent.choice.value}):")
            reasoning_lines.append(f"_{agent.reasoning}_")
            reasoning_lines.append("")

        payoffs = calculate_round_payoffs(tuple(choices))

        round_result = {agent.name: choices[i] for i, agent in enumerate(self.agents)}
        self.history.append(round_result)

        for i, agent in enumerate(self.agents):
            agent.total_score += payoffs[i]

        self.round += 1

        result = "### Round Results\n"
        result += f"**Alice**: {choices[0].value} | **Bob**: {choices[1].value} | **Charlie**: {choices[2].value}\n\n"
        result += "**Payoffs:**\n"
        result += f"- Alice: +{payoffs[0]} (Total: {self.agents[0].total_score})\n"
        result += f"- Bob: +{payoffs[1]} (Total: {self.agents[1].total_score})\n"
        result += f"- Charlie: +{payoffs[2]} (Total: {self.agents[2].total_score})\n"

        return "\n".join(reasoning_lines), result

    def get_current_state(self) -> str:
        if self.round == 0:
            return "### Game Not Started\nClick **Play Round** to begin!"

        state = "### Current Standings\n\n"
        sorted_agents = sorted(self.agents, key=lambda a: a.total_score, reverse=True)
        for i, agent in enumerate(sorted_agents):
            medal = ["🥇", "🥈", "🥉"][i]
            state += f"{medal} **{agent.name}**: {agent.total_score} points\n"
        return state


game = PrisonDilemmaGame()


def play_round_ui():
    reasoning, result = game.play_round()
    state = game.get_current_state()
    history = format_history(game.history)
    return reasoning, result, state, history


def reset_game():
    game.reset()
    return (
        "",
        "",
        "### Game Reset!\nClick **Play Round** to start a new game.",
        "No rounds played yet.",
    )


def format_history(history: list[dict]) -> str:
    if not history:
        return "No rounds played yet."

    lines = ["### Round History\n"]
    for i, round_data in enumerate(history, 1):
        choices = [f"{name}: {choice.value}" for name, choice in round_data.items()]
        lines.append(f"**Round {i}**: {', '.join(choices)}")

    return "\n".join(lines)


with gr.Blocks(title="Prisoner's Dilemma - 3 Agents") as demo:
    gr.Markdown("# Prisoner's Dilemma: 3 AI Agents")
    gr.Markdown("### *Three agents face the ultimate test of trust and betrayal*\n")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Game Controls")
            play_btn = gr.Button("Play Round", variant="primary", size="lg")
            reset_btn = gr.Button("Reset Game", variant="secondary")

        with gr.Column(scale=2):
            game_state = gr.Markdown(value=game.get_current_state())

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Agent Reasoning")
            reasoning_box = gr.Markdown(
                value="*Agents will display their thought process here after each round*"
            )

        with gr.Column():
            gr.Markdown("### Round Result")
            result_box = gr.Markdown(value="*No round played yet*")

    with gr.Row():
        history_box = gr.Markdown(value="No rounds played yet.")

    gr.Markdown("---")
    gr.Markdown("### Payoff Matrix")
    gr.Markdown("""
| Scenario | Alice | Bob | Charlie |
|----------|-------|-----|---------|
| All Cooperate | 4 | 4 | 4 |
| 2 Cooperate, 1 Betray | 1 | 1 | 5 |
| 1 Cooperate, 2 Betray | 0 | 3 | 3 |
| All Betray | 2 | 2 | 2 |
""")

    play_btn.click(
        play_round_ui, outputs=[reasoning_box, result_box, game_state, history_box]
    )

    reset_btn.click(
        reset_game, outputs=[reasoning_box, result_box, game_state, history_box]
    )


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
