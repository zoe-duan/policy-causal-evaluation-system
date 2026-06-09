from pathlib import Path
from causal_policy_system.design_card import load_design_card, validate_design_card, summarize_card, card_to_router_metadata

ROOT = Path(__file__).resolve().parents[1]


def test_example_design_card_validates():
    card = load_design_card(ROOT / "examples" / "design_cards" / "urban_transport_pollution.yaml")
    assert validate_design_card(card) == []
    assert "城市交通限行" in summarize_card(card)
    metadata = card_to_router_metadata(card)
    assert metadata["data_structure"] == "panel"
