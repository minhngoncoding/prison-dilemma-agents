import os
from pathlib import Path
from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task


# Get the config directory relative to this file
CONFIG_DIR = Path(__file__).parent / "config"


def get_llm():
    """Get LLM configuration - supports OpenAI, Ollama, or other providers."""
    base_url = os.getenv("OLLAMA_BASE_URL", "")
    model = os.getenv("MODEL", "gpt-4o-mini")

    if base_url:
        return LLM(
            model=model,
            base_url=base_url,
            api_key="not-needed",
        )
    else:
        return LLM(model=model)


@CrewBase
class PrisonDilemmaCrew:
    """Prisoner's Dilemma Game Crew - orchestrates game with commentary."""

    agents_config = str(CONFIG_DIR / "agents.yaml")
    tasks_config = str(CONFIG_DIR / "tasks.yaml")

    @agent
    def game_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["game_manager"],
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def strategy_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["strategy_analyst"],
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def score_tracker(self) -> Agent:
        return Agent(
            config=self.agents_config["score_tracker"],
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def narrator(self) -> Agent:
        return Agent(
            config=self.agents_config["narrator"],
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def llm_player_1(self) -> Agent:
        return Agent(
            config=self.agents_config["llm_player_1"],
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def llm_player_2(self) -> Agent:
        return Agent(
            config=self.agents_config["llm_player_2"],
            llm=get_llm(),
            verbose=True,
        )

    @agent
    def always_cooperate(self) -> Agent:
        return Agent(
            config=self.agents_config["always_cooperate"],
            verbose=True,
        )

    @agent
    def always_betray(self) -> Agent:
        return Agent(
            config=self.agents_config["always_betray"],
            verbose=True,
        )

    @agent
    def random_player(self) -> Agent:
        return Agent(
            config=self.agents_config["random_player"],
            verbose=True,
        )

    @agent
    def tit_for_tat(self) -> Agent:
        return Agent(
            config=self.agents_config["tit_for_tat"],
            verbose=True,
        )

    @agent
    def tit_for_two_tats(self) -> Agent:
        return Agent(
            config=self.agents_config["tit_for_two_tats"],
            verbose=True,
        )

    @agent
    def two_tits_for_tat(self) -> Agent:
        return Agent(
            config=self.agents_config["two_tits_for_tat"],
            verbose=True,
        )

    @agent
    def grudger(self) -> Agent:
        return Agent(
            config=self.agents_config["grudger"],
            verbose=True,
        )

    @agent
    def aggressive(self) -> Agent:
        return Agent(
            config=self.agents_config["aggressive"],
            verbose=True,
        )

    @agent
    def adaptive(self) -> Agent:
        return Agent(
            config=self.agents_config["adaptive"],
            verbose=True,
        )

    @agent
    def optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config["optimizer"],
            verbose=True,
        )

    @agent
    def probabilistic_cooperator(self) -> Agent:
        return Agent(
            config=self.agents_config["probabilistic_cooperator"],
            verbose=True,
        )

    @agent
    def signaler(self) -> Agent:
        return Agent(
            config=self.agents_config["signaler"],
            verbose=True,
        )

    @task
    def initialize_game(self) -> Task:
        return Task(
            config=self.tasks_config["initialize_game"],
        )

    @task
    def collect_decisions(self) -> Task:
        return Task(
            config=self.tasks_config["collect_decisions"],
        )

    @task
    def analyze_round_result(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_round_result"],
        )

    @task
    def update_scores(self) -> Task:
        return Task(
            config=self.tasks_config["update_scores"],
        )

    @task
    def generate_round_narrative(self) -> Task:
        return Task(
            config=self.tasks_config["generate_round_narrative"],
        )

    @task
    def check_game_end(self) -> Task:
        return Task(
            config=self.tasks_config["check_game_end"],
        )

    @task
    def generate_final_report(self) -> Task:
        return Task(
            config=self.tasks_config["generate_final_report"],
        )

    @task
    def generate_tournament_summary(self) -> Task:
        return Task(
            config=self.tasks_config["generate_tournament_summary"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Prisoner's Dilemma Game Crew."""
        return Crew(
            agents=self.agents,  # Automatically assembled from @agent decorators
            tasks=self.tasks,  # Automatically assembled from @task decorators
            process=Process.sequential,
            verbose=True,
        )

    @staticmethod
    def get_player_agent(strategy_name: str) -> str:
        """Get agent key for a given strategy name."""
        strategy_map = {
            "always_cooperate": "always_cooperate",
            "always_betray": "always_betray",
            "random": "random_player",
            "tit_for_tat": "tit_for_tat",
            "tit_for_two_tats": "tit_for_two_tats",
            "two_tits_for_tat": "two_tits_for_tat",
            "grudger": "grudger",
            "aggressive": "aggressive",
            "adaptive": "adaptive",
            "optimizer": "optimizer",
            "probabilistic_cooperator": "probabilistic_cooperator",
            "signaler": "signaler",
            "llm_player_1": "llm_player_1",
            "llm_player_2": "llm_player_2",
        }
        return strategy_map.get(strategy_name.lower(), "always_cooperate")

    @staticmethod
    def list_available_strategies() -> list[str]:
        """List all available player strategies."""
        return [
            "always_cooperate",
            "always_betray",
            "random",
            "tit_for_tat",
            "tit_for_two_tats",
            "two_tits_for_tat",
            "grudger",
            "aggressive",
            "adaptive",
            "optimizer",
            "probabilistic_cooperator",
            "signaler",
            "llm_player_1",
            "llm_player_2",
        ]
