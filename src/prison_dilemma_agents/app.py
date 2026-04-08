"""
Prisoner's Dilemma Game - UI Launcher

Launch the Gradio interface for playing the game.
"""

from prison_dilemma_agents.ui.gradio_app import create_ui


def launch():
    """Launch the Gradio UI."""
    demo = create_ui()
    demo.launch()


if __name__ == "__main__":
    launch()
