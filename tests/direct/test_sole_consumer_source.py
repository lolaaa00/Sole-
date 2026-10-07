"""Static security checks for the second contract.

The pinned Direct Mode loader supports one Contract subclass per process and
cannot emulate IC-to-IC dispatch. These checks protect the consumer binding
surface locally; real dispatch remains a mandatory Studionet lifecycle case.
"""

from pathlib import Path


SOURCE = Path("contracts/sole_consumer.py").read_text()


def test_consumer_pins_exact_sole_book_and_hashes():
    for marker in (
        "self.sole_address = sole_address",
        "self.book_id = book_id",
        "self.book_hash = str(book_hash).strip().lower()",
        'item.get("book_id", -1)',
        'item.get("book_hash", "")',
        'item.get("reservation_hash", "")',
        "sole.view().is_granted(",
    ):
        assert marker in SOURCE


def test_consumer_checks_holder_and_replay():
    assert "only reservation holder may activate" in SOURCE
    assert "reservation already activated" in SOURCE
    assert "if key in self.activations" in SOURCE


def test_consumer_rejects_zero_dependency_and_malformed_hashes():
    assert "sole_address cannot be zero address" in SOURCE
    assert "is_lower_hex_digest(book_hash)" in SOURCE
    assert "is_lower_hex_digest(expected_reservation_hash)" in SOURCE
