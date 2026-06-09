"""Codex-native causal inference and policy evaluation toolkit."""

from .method_router import MethodRecommendation, recommend_methods
from .design_card import load_design_card, validate_design_card

__all__ = [
    "MethodRecommendation",
    "recommend_methods",
    "load_design_card",
    "validate_design_card",
    "design_card",
    "estimators",
    "method_router",
    "policy_documents",
    "reporting",
    "study_orchestrator",
]

__version__ = "0.1.0"
