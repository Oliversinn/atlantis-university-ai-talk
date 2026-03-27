"""Configuration constants for the F1 AI Assistant."""

from datetime import datetime

CACHE_DIR = "cache"

CURRENT_YEAR = datetime.now().year

EXAMPLE_QUESTIONS = [
    "Who has the most Formula 1 World Championships?",
    "What is DRS and how does it work?",
    "Show me the lap times from the 2023 Monaco Grand Prix",
    "Who won the most races in 2023?",
    "What are the 2024 F1 technical regulations about the cost cap?",
    "Show me the race results for the 2023 British Grand Prix",
    "Which team scored the most points in 2023?",
    "Who holds the record for most pole positions?",
    "Explain the tire compound strategy used in modern F1",
    "Show me the 2023 driver championship standings",
]

OPENAI_MODEL = "gpt-4o-mini"
