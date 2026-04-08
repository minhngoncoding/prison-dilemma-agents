#!/usr/bin/env python
"""
Prisoner's Dilemma Game - Main Entry Point

Usage:
    python -m prison_dilemma_agents.main run          # Run a game
    python -m prison_dilemma_agents.main train 5 file # Train crew
    python -m prison_dilemma_agents.main test 5 gpt-4o # Test crew
"""

import sys
import warnings

from prison_dilemma_agents.crew import PrisonDilemmaCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the Prisoner's Dilemma game crew.
    """
    inputs = {
        "player_1_name": "Alice",
        "player_2_name": "Bob",
        "player_1_strategy": "tit_for_tat",
        "player_2_strategy": "always_betray",
        "number_of_rounds": 10,
    }

    try:
        PrisonDilemmaCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "player_1_name": "Alice",
        "player_2_name": "Bob",
        "player_1_strategy": "tit_for_tat",
        "player_2_strategy": "always_betray",
        "number_of_rounds": 10,
    }

    try:
        PrisonDilemmaCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        PrisonDilemmaCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "player_1_name": "Alice",
        "player_2_name": "Bob",
        "player_1_strategy": "tit_for_tat",
        "player_2_strategy": "always_betray",
        "number_of_rounds": 10,
    }

    try:
        PrisonDilemmaCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def ui():
    """
    Launch the Gradio UI.
    """
    import os
    from prison_dilemma_agents.ui.gradio_app import create_ui

    demo = create_ui()
    # Use env var or default to 7860
    port = int(os.getenv("GRADIO_SERVER_PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "ui"

    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    elif command == "ui":
        ui()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: run, train, replay, test, ui")
