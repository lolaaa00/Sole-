# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
# Stable Studionet 61999 consumer example.

from genlayer import *

from dataclasses import dataclass


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def is_lower_hex_digest(value: str) -> bool:
    text = str(value).strip()
    if len(text) != 64 or text != text.lower():
        return False
    return all(char in "0123456789abcdef" for char in text)


@gl.contract_interface
class ISole:
    class View:
        def get_reservation(self, reservation_id: u256) -> dict: ...
        def is_granted(
            self,
            reservation_id: u256,
            expected_reservation_hash: str,
            expected_book_hash: str,
        ) -> bool: ...

    class Write:
        pass


@allow_storage
@dataclass
class ActivationReceipt:
    holder: Address
    reservation_id: u256
    reservation_hash: str
    book_hash: str


class SoleConsumer(gl.Contract):
    """Minimal consumer proving another IC can rely on a SOLE grant.

    This contract does not interpret semantic scopes. It binds one canonical
    SOLE book at construction and allows the recorded holder of a granted
    reservation to activate exactly once.

    Time semantics deliberately remain outside this tiny demo consumer:
    `GRANTED` means SOLE issued the immutable reservation covering its declared
    [start_at,end_at) interval. Production consumers that need "effective now"
    should enforce the declared interval using their own trusted execution-time
    context rather than inventing time inside a cross-contract view.
    """

    sole_address: Address
    book_id: u256
    book_hash: str
    activations: TreeMap[str, ActivationReceipt]
    activation_count: u256

    def __init__(
        self,
        sole_address: Address,
        book_id: u256,
        book_hash: str,
    ):
        if str(sole_address).lower() == ZERO_ADDRESS:
            raise gl.vm.UserError("EXPECTED: sole_address cannot be zero address")
        if not is_lower_hex_digest(book_hash):
            raise gl.vm.UserError("EXPECTED: book_hash must be 32-byte lowercase hex")
        self.sole_address = sole_address
        self.book_id = book_id
        self.book_hash = str(book_hash).strip().lower()
        self.activation_count = u256(0)

    @gl.public.write
    def activate(
        self,
        reservation_id: u256,
        expected_reservation_hash: str,
    ) -> None:
        if not is_lower_hex_digest(expected_reservation_hash):
            raise gl.vm.UserError(
                "EXPECTED: reservation hash must be 32-byte lowercase hex"
            )
        sole = ISole(self.sole_address)
        item = sole.view().get_reservation(reservation_id)

        if int(item.get("book_id", -1)) != int(self.book_id):
            raise gl.vm.UserError("EXPECTED: reservation belongs to a different SOLE book")
        if str(item.get("book_hash", "")).lower() != self.book_hash:
            raise gl.vm.UserError("EXPECTED: reservation book hash mismatch")
        if str(item.get("reservation_hash", "")).lower() != str(expected_reservation_hash).strip().lower():
            raise gl.vm.UserError("EXPECTED: reservation hash mismatch")
        if str(item.get("holder", "")).lower() != str(gl.message.sender_address).lower():
            raise gl.vm.UserError("EXPECTED: only reservation holder may activate")

        if not sole.view().is_granted(
            reservation_id,
            expected_reservation_hash,
            self.book_hash,
        ):
            raise gl.vm.UserError("EXPECTED: SOLE reservation is not granted")

        key = str(expected_reservation_hash).strip().lower()
        if key in self.activations:
            raise gl.vm.UserError("EXPECTED: reservation already activated")

        self.activations[key] = ActivationReceipt(
            holder=gl.message.sender_address,
            reservation_id=reservation_id,
            reservation_hash=key,
            book_hash=self.book_hash,
        )
        self.activation_count = u256(int(self.activation_count) + 1)

    @gl.public.view
    def was_activated(self, reservation_hash: str) -> bool:
        return str(reservation_hash).strip().lower() in self.activations

    @gl.public.view
    def get_activation_count(self) -> u256:
        return self.activation_count
