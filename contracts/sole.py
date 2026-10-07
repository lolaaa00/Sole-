# Stable Studionet 61999 contract.
# Runtime dependency reused from proven 61999-era repositories.
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

import json
from dataclasses import dataclass
import typing


# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------

BOOK_DRAFT = 0
BOOK_SEALED = 1

RES_PROPOSED = 0
RES_ACCEPTED = 1
RES_READY = 2
RES_BLOCKED = 3
RES_AMBIGUOUS = 4
RES_GRANTED = 5
RES_RELEASED = 6
RES_WITHDRAWN = 7
RES_ASSESS_EXHAUSTED = 8

STATUS_NAMES = {
    RES_PROPOSED: "PROPOSED",
    RES_ACCEPTED: "ACCEPTED",
    RES_READY: "READY",
    RES_BLOCKED: "BLOCKED",
    RES_AMBIGUOUS: "AMBIGUOUS",
    RES_GRANTED: "GRANTED",
    RES_RELEASED: "RELEASED",
    RES_WITHDRAWN: "WITHDRAWN",
    RES_ASSESS_EXHAUSTED: "ASSESS_EXHAUSTED",
}

REL_EQUIVALENT = "EQUIVALENT"
REL_CONTAINS = "CONTAINS"
REL_CONTAINED_BY = "CONTAINED_BY"
REL_OVERLAPS = "OVERLAPS"
REL_DISJOINT = "DISJOINT"
REL_AMBIGUOUS = "AMBIGUOUS"

ALLOWED_RELATIONS = (
    REL_EQUIVALENT,
    REL_CONTAINS,
    REL_CONTAINED_BY,
    REL_OVERLAPS,
    REL_DISJOINT,
    REL_AMBIGUOUS,
)

PAIR_CLEAR = "CLEAR"
PAIR_CONFLICT = "CONFLICT"
PAIR_AMBIGUOUS = "AMBIGUOUS"

OUTCOME_SUBSTANTIVE = "SUBSTANTIVE"
OUTCOME_MODEL_OUTPUT_INVALID = "MODEL_OUTPUT_INVALID"
OUTCOME_SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
NON_DECISION_OUTCOMES = (
    OUTCOME_MODEL_OUTPUT_INVALID,
    OUTCOME_SOURCE_UNAVAILABLE,
)

DIMENSIONS = ("right", "product", "territory", "channel", "audience")

MAX_NAME_LEN = 96
MAX_DOMAIN_KEY_LEN = 96
MAX_CHARTER_LEN = 3500
MAX_SCOPE_LEN = 420
MAX_REASON_LEN = 900
MAX_RESERVATIONS_PER_BOOK = 48
MAX_COMPARISON_SET = 12
MAX_NONDECISION_ATTEMPTS = 12
MAX_WINDOW_SECONDS = 10 * 365 * 24 * 60 * 60

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ERR_EXPECTED = "EXPECTED"
PROTOCOL_VERSION = "SOLE/1"


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

@allow_storage
@dataclass
class ExclusivityBook:
    owner: Address
    name: str
    domain_key: str
    semantic_charter: str
    status: u8
    active: bool
    definition_hash: str
    epoch: u256
    reservation_ids: DynArray[u256]


@allow_storage
@dataclass
class Reservation:
    book_id: u256
    book_hash: str
    grantor: Address
    holder: Address
    right_scope: str
    product_scope: str
    territory_scope: str
    channel_scope: str
    audience_scope: str
    start_at: u256
    end_at: u256
    reservation_hash: str
    status: u8
    holder_accepted: bool
    created_at: u256
    assessed_at: u256
    assessed_epoch: u256
    comparison_set_hash: str
    conflict_ids: DynArray[u256]
    ambiguous_ids: DynArray[u256]
    assessment_attempts: u32
    consecutive_nondecisions: u32
    last_assessment_result: str
    reason: str
    granted_at: u256
    released_at: u256


# ---------------------------------------------------------------------------
# Reusable interface
# ---------------------------------------------------------------------------

@gl.contract_interface
class ISole:
    class View:
        def get_book(self, book_id: u256) -> dict: ...
        def get_reservation(self, reservation_id: u256) -> dict: ...
        def is_granted(
            self,
            reservation_id: u256,
            expected_reservation_hash: str,
            expected_book_hash: str,
        ) -> bool: ...
        def get_protocol_dictionary(self) -> dict: ...

    class Write:
        def assess_reservation(self, reservation_id: u256) -> None: ...
        def finalize_grant(self, reservation_id: u256) -> None: ...


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class BookCreated(gl.Event):
    def __init__(self, book_id: u256, owner: Address, /, **blob): ...

class BookSealed(gl.Event):
    def __init__(self, book_id: u256, definition_hash: str, /, **blob): ...

class BookActivationChanged(gl.Event):
    def __init__(self, active: bool, book_id: u256, /, **blob): ...

class ReservationProposed(gl.Event):
    def __init__(self, holder: Address, reservation_id: u256, /, **blob): ...

class ReservationAccepted(gl.Event):
    def __init__(self, holder: Address, reservation_id: u256, /, **blob): ...

class ReservationAssessed(gl.Event):
    def __init__(self, reservation_id: u256, result: str, /, **blob): ...

class ReservationAssessmentNonDecision(gl.Event):
    def __init__(self, outcome: str, reservation_id: u256, /, **blob): ...

class ReservationAssessmentExhausted(gl.Event):
    def __init__(self, attempts: u32, reservation_id: u256, /, **blob): ...

class ReservationGranted(gl.Event):
    def __init__(self, holder: Address, reservation_id: u256, /, **blob): ...

class ReservationReleased(gl.Event):
    def __init__(self, holder: Address, reservation_id: u256, /, **blob): ...

class ReservationWithdrawn(gl.Event):
    def __init__(self, actor: Address, reservation_id: u256, /, **blob): ...


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------

def clean_text(value: typing.Any, limit: int) -> str:
    return " ".join(str(value).strip().split())[:limit]


def bounded_text(value: typing.Any, limit: int, field: str) -> str:
    """Canonicalize protocol input without silently changing its meaning."""
    text = " ".join(str(value).strip().split())
    if text == "":
        raise gl.vm.UserError(f"{ERR_EXPECTED}: {field} is required")
    if len(text) > limit:
        raise gl.vm.UserError(
            f"{ERR_EXPECTED}: {field} exceeds maximum length {limit}"
        )
    return text


def normalise_domain_key(value: str) -> str:
    text = bounded_text(value, MAX_DOMAIN_KEY_LEN, "domain_key").upper().replace(" ", "_")
    for char in text:
        if char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:_-.":
            raise gl.vm.UserError(
                f"{ERR_EXPECTED}: domain_key may only contain A-Z, 0-9, :, _, -, ."
            )
    return text


def message_timestamp() -> int:
    message = getattr(gl, "message", None)
    raw_message = getattr(message, "raw", None)
    raw = getattr(raw_message, "datetime", None)
    if raw in (None, ""):
        mapping = getattr(gl, "message_raw", None)
        raw = mapping.get("datetime", "") if isinstance(mapping, dict) else ""
    if isinstance(raw, int):
        return int(raw)
    if not isinstance(raw, str) or raw.strip() == "":
        # Timestamp is evidence metadata only for creation/grant/release in
        # SOLE. Conflict safety never depends on wall-clock "now", so fail
        # closed rather than synthesising time.
        raise gl.vm.UserError(f"{ERR_EXPECTED}: transaction timestamp is unavailable")
    from datetime import datetime, timezone
    parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def is_zero_address(address: Address) -> bool:
    return str(address).lower() == ZERO_ADDRESS.lower()


def canonical_json(value: typing.Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: typing.Any) -> str:
    return Keccak256(canonical_json(value).encode("utf-8")).hexdigest()


def book_definition_hash(
    owner: str,
    name: str,
    domain_key: str,
    semantic_charter: str,
) -> str:
    return digest_json({
        "protocol": PROTOCOL_VERSION,
        "owner": str(owner).lower(),
        "name": name,
        "domain_key": domain_key,
        "semantic_charter": semantic_charter,
    })


def reservation_definition_hash(
    reservation_id: int,
    book_id: int,
    book_hash: str,
    grantor: str,
    holder: str,
    right_scope: str,
    product_scope: str,
    territory_scope: str,
    channel_scope: str,
    audience_scope: str,
    start_at: int,
    end_at: int,
) -> str:
    return digest_json({
        "protocol": PROTOCOL_VERSION,
        "reservation_id": reservation_id,
        "book_id": book_id,
        "book_hash": book_hash,
        "grantor": str(grantor).lower(),
        "holder": str(holder).lower(),
        "right_scope": right_scope,
        "product_scope": product_scope,
        "territory_scope": territory_scope,
        "channel_scope": channel_scope,
        "audience_scope": audience_scope,
        "start_at": start_at,
        "end_at": end_at,
    })


def intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    # Half-open intervals [start,end). Boundary-touching reservations do not
    # overlap: one may end at the exact instant the next begins.
    return int(a_start) < int(b_end) and int(b_start) < int(a_end)


def parse_json_object(raw: typing.Any) -> typing.Optional[dict]:
    if isinstance(raw, dict):
        return raw
    text = str(raw).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        value = json.loads(text)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def normalise_relation(value: typing.Any) -> typing.Optional[str]:
    relation = clean_text(value, 32).upper().replace("-", "_").replace(" ", "_")
    return relation if relation in ALLOWED_RELATIONS else None


def pair_outcome(relations: dict[str, str]) -> str:
    # One definitely-disjoint dimension is enough to establish that the
    # scopes do not collide, regardless of ambiguity in a different
    # dimension. With no disjoint dimension, any ambiguity fails closed.
    if any(relations[key] == REL_DISJOINT for key in DIMENSIONS):
        return PAIR_CLEAR
    if any(relations[key] == REL_AMBIGUOUS for key in DIMENSIONS):
        return PAIR_AMBIGUOUS
    return PAIR_CONFLICT


def canonical_model_result(
    raw: typing.Any,
    expected_ids: list[int],
    comparison_set_hash: str,
) -> typing.Optional[dict]:
    parsed = parse_json_object(raw)
    if parsed is None:
        return None
    items = parsed.get("comparisons")
    if not isinstance(items, list):
        return None

    expected = [int(item) for item in expected_ids]
    if len(items) != len(expected):
        return None

    by_id: dict[int, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            return None
        try:
            incumbent_id = int(item.get("incumbent_id"))
        except Exception:
            return None
        if incumbent_id in by_id:
            return None
        relations: dict[str, str] = {}
        for key in DIMENSIONS:
            relation = normalise_relation(item.get(key))
            if relation is None:
                return None
            relations[key] = relation
        by_id[incumbent_id] = {
            "incumbent_id": incumbent_id,
            "relations": relations,
            "pair_outcome": pair_outcome(relations),
            "reason_code": clean_text(item.get("reason_code", ""), 80),
        }

    if sorted(by_id.keys()) != sorted(expected):
        return None

    conflict_ids: list[int] = []
    ambiguous_ids: list[int] = []
    clear_ids: list[int] = []
    canonical_items: list[dict] = []
    for incumbent_id in expected:
        item = by_id[incumbent_id]
        canonical_items.append(item)
        if item["pair_outcome"] == PAIR_CONFLICT:
            conflict_ids.append(incumbent_id)
        elif item["pair_outcome"] == PAIR_AMBIGUOUS:
            ambiguous_ids.append(incumbent_id)
        else:
            clear_ids.append(incumbent_id)

    if conflict_ids:
        overall = PAIR_CONFLICT
    elif ambiguous_ids:
        overall = PAIR_AMBIGUOUS
    else:
        overall = PAIR_CLEAR

    return {
        "outcome": OUTCOME_SUBSTANTIVE,
        "comparison_set_hash": comparison_set_hash,
        "incumbent_ids": expected,
        "conflict_ids": conflict_ids,
        "ambiguous_ids": ambiguous_ids,
        "clear_ids": clear_ids,
        "overall": overall,
        "comparisons": canonical_items,
    }


def relation_prompt(
    book: ExclusivityBook,
    candidate_id: int,
    candidate: Reservation,
    incumbents: list[tuple[int, Reservation]],
    comparison_set_hash: str,
) -> str:
    payload = {
        "protocol": PROTOCOL_VERSION,
        "book": {
            "name": book.name,
            "domain_key": book.domain_key,
            "semantic_charter": book.semantic_charter,
        },
        "candidate": {
            "reservation_id": candidate_id,
            "right": candidate.right_scope,
            "product": candidate.product_scope,
            "territory": candidate.territory_scope,
            "channel": candidate.channel_scope,
            "audience": candidate.audience_scope,
            "start_at": int(candidate.start_at),
            "end_at": int(candidate.end_at),
        },
        "incumbents": [
            {
                "reservation_id": incumbent_id,
                "right": item.right_scope,
                "product": item.product_scope,
                "territory": item.territory_scope,
                "channel": item.channel_scope,
                "audience": item.audience_scope,
                "start_at": int(item.start_at),
                "end_at": int(item.end_at),
            }
            for incumbent_id, item in incumbents
        ],
        "comparison_set_hash": comparison_set_hash,
    }

    return f"""
SOLE semantic exclusivity overlap assessor.

You are not deciding legality, fairness, pricing, ownership, or whether anyone
"deserves" exclusivity. You perform one bounded task: compare one candidate
reservation with every incumbent reservation supplied under the frozen book
charter.

All listed pairs already overlap in time. For EACH incumbent, classify these
five semantic dimensions independently:
- right
- product
- territory
- channel
- audience

Allowed relation labels are EXACTLY:
EQUIVALENT
CONTAINS
CONTAINED_BY
OVERLAPS
DISJOINT
AMBIGUOUS

Meanings:
- EQUIVALENT: materially the same scope.
- CONTAINS: candidate dimension wholly contains incumbent dimension.
- CONTAINED_BY: candidate dimension is wholly contained by incumbent dimension.
- OVERLAPS: non-empty material intersection, but neither clearly contains the other.
- DISJOINT: no material intersection for that dimension.
- AMBIGUOUS: the supplied wording/charter is insufficient to decide safely.

Do not infer unstated exclusions. Do not "fix" or rewrite the rights. Do not
decide the overall conflict yourself; the contract derives it deterministically:
a pair is CLEAR if ANY dimension is DISJOINT; otherwise AMBIGUOUS if ANY
dimension is AMBIGUOUS; otherwise CONFLICT.

Return JSON only:
{{
  "comparisons": [
    {{
      "incumbent_id": <integer>,
      "right": "<allowed relation>",
      "product": "<allowed relation>",
      "territory": "<allowed relation>",
      "channel": "<allowed relation>",
      "audience": "<allowed relation>",
      "reason_code": "<short uppercase token>"
    }}
  ]
}}

Return exactly one item for each incumbent_id and no extras.

Frozen input:
{canonical_json(payload)}
""".strip()


def comparison_set_digest(
    candidate_hash: str,
    epoch: int,
    incumbents: list[tuple[int, Reservation]],
) -> str:
    return digest_json({
        "protocol": PROTOCOL_VERSION,
        "candidate_hash": candidate_hash,
        "epoch": int(epoch),
        "incumbents": [
            {"id": int(reservation_id), "hash": str(item.reservation_hash)}
            for reservation_id, item in incumbents
        ],
    })


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class Sole(gl.Contract):
    """Consensus-backed semantic exclusivity reservation primitive.

    The issuer creates one immutable book per canonical domain_key. Proposed
    exclusive rights are immutable and require holder acceptance. When a
    candidate's declared time window overlaps already-granted rights, GenLayer
    consensus compares the semantic scopes. Deterministic code derives whether
    the candidate is CLEAR, CONFLICTING, or AMBIGUOUS.

    A book epoch eliminates TOCTOU: every grant/release increments the epoch,
    invalidating all previously assessed-but-ungranted candidates. The owner
    must re-assess against the new incumbent set before granting.

    SOLE does not decide legal validity. It prevents this canonical registry
    from issuing two materially overlapping exclusive reservations inside the
    same immutable book/domain.
    """

    books: TreeMap[u256, ExclusivityBook]
    reservations: TreeMap[u256, Reservation]
    book_by_owner_domain: TreeMap[str, u256]
    next_book_id: u256
    next_reservation_id: u256

    def __init__(self):
        self.next_book_id = u256(1)
        self.next_reservation_id = u256(1)

    def _require_book(self, book_id: u256) -> ExclusivityBook:
        if book_id not in self.books:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: unknown book")
        return self.books[book_id]

    def _require_reservation(self, reservation_id: u256) -> Reservation:
        if reservation_id not in self.reservations:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: unknown reservation")
        return self.reservations[reservation_id]

    def _require_owner(self, book: ExclusivityBook) -> None:
        if str(book.owner).lower() != str(gl.message.sender_address).lower():
            raise gl.vm.UserError(f"{ERR_EXPECTED}: only book owner")

    def _owner_domain_key(self, owner: Address, domain_key: str) -> str:
        return f"{str(owner).lower()}|{domain_key}"

    def _current_book_hash(self, book: ExclusivityBook) -> str:
        return book_definition_hash(
            str(book.owner),
            book.name,
            book.domain_key,
            book.semantic_charter,
        )

    def _current_reservation_hash(self, reservation_id: int, item: Reservation) -> str:
        return reservation_definition_hash(
            reservation_id,
            int(item.book_id),
            item.book_hash,
            str(item.grantor),
            str(item.holder),
            item.right_scope,
            item.product_scope,
            item.territory_scope,
            item.channel_scope,
            item.audience_scope,
            int(item.start_at),
            int(item.end_at),
        )

    def _candidate_incumbents(
        self,
        reservation_id: int,
        item: Reservation,
        book: ExclusivityBook,
    ) -> list[tuple[int, Reservation]]:
        incumbents: list[tuple[int, Reservation]] = []
        for raw_id in book.reservation_ids:
            incumbent_id = int(raw_id)
            if incumbent_id == reservation_id:
                continue
            if raw_id not in self.reservations:
                continue
            other = self.reservations[raw_id]
            if int(other.status) != RES_GRANTED:
                continue
            if not intervals_overlap(
                int(item.start_at), int(item.end_at),
                int(other.start_at), int(other.end_at),
            ):
                continue
            incumbents.append((incumbent_id, other))
            if len(incumbents) > MAX_COMPARISON_SET:
                raise gl.vm.UserError(
                    f"{ERR_EXPECTED}: too many time-overlapping incumbent rights "
                    f"(>{MAX_COMPARISON_SET}); use a narrower canonical domain book"
                )
        return incumbents

    # ------------------------------------------------------------------
    # Book lifecycle
    # ------------------------------------------------------------------

    @gl.public.write
    def create_book(
        self,
        name: str,
        domain_key: str,
        semantic_charter: str,
    ) -> u256:
        name = bounded_text(name, MAX_NAME_LEN, "name")
        domain_key = normalise_domain_key(domain_key)
        semantic_charter = bounded_text(
            semantic_charter, MAX_CHARTER_LEN, "semantic_charter"
        )

        owner = gl.message.sender_address
        uniqueness_key = self._owner_domain_key(owner, domain_key)
        if uniqueness_key in self.book_by_owner_domain:
            raise gl.vm.UserError(
                f"{ERR_EXPECTED}: owner already has a canonical book for this domain_key"
            )

        book_id = self.next_book_id
        self.next_book_id = u256(int(self.next_book_id) + 1)
        self.books[book_id] = ExclusivityBook(
            owner=owner,
            name=name,
            domain_key=domain_key,
            semantic_charter=semantic_charter,
            status=u8(BOOK_DRAFT),
            active=False,
            definition_hash="",
            epoch=u256(0),
            reservation_ids=[],
        )
        self.book_by_owner_domain[uniqueness_key] = book_id
        BookCreated(book_id, owner, name=name, domain_key=domain_key).emit()
        return book_id

    @gl.public.write
    def seal_book(self, book_id: u256) -> str:
        book = self._require_book(book_id)
        self._require_owner(book)
        if int(book.status) != BOOK_DRAFT:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book already sealed")
        digest = self._current_book_hash(book)
        book.definition_hash = digest
        book.status = u8(BOOK_SEALED)
        book.active = True
        BookSealed(book_id, digest).emit()
        return digest

    @gl.public.write
    def set_book_active(self, book_id: u256, active: bool) -> None:
        book = self._require_book(book_id)
        self._require_owner(book)
        if int(book.status) != BOOK_SEALED:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book is not sealed")
        book.active = bool(active)
        BookActivationChanged(bool(active), book_id).emit()

    # ------------------------------------------------------------------
    # Reservation lifecycle
    # ------------------------------------------------------------------

    @gl.public.write
    def propose_reservation(
        self,
        book_id: u256,
        holder: Address,
        right_scope: str,
        product_scope: str,
        territory_scope: str,
        channel_scope: str,
        audience_scope: str,
        start_at: u256,
        end_at: u256,
    ) -> u256:
        book = self._require_book(book_id)
        self._require_owner(book)
        if int(book.status) != BOOK_SEALED or not bool(book.active):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book is not active and sealed")
        if str(book.definition_hash) != self._current_book_hash(book):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book definition hash mismatch")
        if is_zero_address(holder):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: holder cannot be zero address")
        if len(book.reservation_ids) >= MAX_RESERVATIONS_PER_BOOK:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation limit reached")

        right_scope = bounded_text(right_scope, MAX_SCOPE_LEN, "right_scope")
        product_scope = bounded_text(product_scope, MAX_SCOPE_LEN, "product_scope")
        territory_scope = bounded_text(
            territory_scope, MAX_SCOPE_LEN, "territory_scope"
        )
        channel_scope = bounded_text(channel_scope, MAX_SCOPE_LEN, "channel_scope")
        audience_scope = bounded_text(
            audience_scope, MAX_SCOPE_LEN, "audience_scope"
        )

        start_i = int(start_at)
        end_i = int(end_at)
        if start_i < 0 or end_i <= start_i:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: invalid reservation interval")
        if end_i - start_i > MAX_WINDOW_SECONDS:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation interval exceeds protocol maximum")

        reservation_id = self.next_reservation_id
        self.next_reservation_id = u256(int(self.next_reservation_id) + 1)
        digest = reservation_definition_hash(
            int(reservation_id),
            int(book_id),
            book.definition_hash,
            str(book.owner),
            str(holder),
            right_scope,
            product_scope,
            territory_scope,
            channel_scope,
            audience_scope,
            start_i,
            end_i,
        )

        self.reservations[reservation_id] = Reservation(
            book_id=book_id,
            book_hash=book.definition_hash,
            grantor=book.owner,
            holder=holder,
            right_scope=right_scope,
            product_scope=product_scope,
            territory_scope=territory_scope,
            channel_scope=channel_scope,
            audience_scope=audience_scope,
            start_at=start_at,
            end_at=end_at,
            reservation_hash=digest,
            status=u8(RES_PROPOSED),
            holder_accepted=False,
            created_at=u256(message_timestamp()),
            assessed_at=u256(0),
            assessed_epoch=u256(0),
            comparison_set_hash="",
            conflict_ids=[],
            ambiguous_ids=[],
            assessment_attempts=u32(0),
            consecutive_nondecisions=u32(0),
            last_assessment_result="",
            reason="",
            granted_at=u256(0),
            released_at=u256(0),
        )
        book.reservation_ids.append(reservation_id)
        ReservationProposed(
            holder,
            reservation_id,
            book_id=int(book_id),
            reservation_hash=digest,
        ).emit()
        return reservation_id

    @gl.public.write
    def accept_reservation(self, reservation_id: u256) -> None:
        item = self._require_reservation(reservation_id)
        if int(item.status) != RES_PROPOSED:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation is not proposed")
        if str(item.holder).lower() != str(gl.message.sender_address).lower():
            raise gl.vm.UserError(f"{ERR_EXPECTED}: only proposed holder")
        if str(item.reservation_hash) != self._current_reservation_hash(int(reservation_id), item):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation definition hash mismatch")
        item.holder_accepted = True
        item.status = u8(RES_ACCEPTED)
        ReservationAccepted(item.holder, reservation_id).emit()

    @gl.public.write
    def withdraw_reservation(self, reservation_id: u256) -> None:
        item = self._require_reservation(reservation_id)
        if int(item.status) in (RES_GRANTED, RES_RELEASED, RES_WITHDRAWN):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation cannot be withdrawn")
        sender = str(gl.message.sender_address).lower()
        if sender not in (str(item.grantor).lower(), str(item.holder).lower()):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: only grantor or holder")
        item.status = u8(RES_WITHDRAWN)
        ReservationWithdrawn(gl.message.sender_address, reservation_id).emit()

    def _observe(
        self,
        book: ExclusivityBook,
        reservation_id: int,
        item: Reservation,
        incumbents: list[tuple[int, Reservation]],
        comparison_hash: str,
    ) -> dict:
        try:
            raw = gl.nondet.exec_prompt(
                relation_prompt(book, reservation_id, item, incumbents, comparison_hash),
                response_format="text",
            )
        except Exception as error:
            return {
                "outcome": OUTCOME_SOURCE_UNAVAILABLE,
                "reason": clean_text(f"model call failed: {error}", MAX_REASON_LEN),
            }

        parsed = canonical_model_result(
            raw,
            [incumbent_id for incumbent_id, _ in incumbents],
            comparison_hash,
        )
        if parsed is None:
            return {
                "outcome": OUTCOME_MODEL_OUTPUT_INVALID,
                "reason": "overlap assessor output could not be parsed into the fixed protocol shape",
            }
        return parsed

    def _substantive_shape_valid(
        self,
        value: typing.Any,
        expected_ids: list[int],
        comparison_hash: str,
    ) -> bool:
        if not isinstance(value, dict):
            return False
        if value.get("outcome") != OUTCOME_SUBSTANTIVE:
            return False
        if str(value.get("comparison_set_hash", "")) != comparison_hash:
            return False
        try:
            incumbent_ids = [int(v) for v in value.get("incumbent_ids", [])]
            conflict_ids = [int(v) for v in value.get("conflict_ids", [])]
            ambiguous_ids = [int(v) for v in value.get("ambiguous_ids", [])]
            clear_ids = [int(v) for v in value.get("clear_ids", [])]
        except Exception:
            return False
        if incumbent_ids != expected_ids:
            return False
        all_ids = conflict_ids + ambiguous_ids + clear_ids
        if len(all_ids) != len(set(all_ids)):
            return False
        if sorted(all_ids) != sorted(expected_ids):
            return False
        if conflict_ids:
            expected_overall = PAIR_CONFLICT
        elif ambiguous_ids:
            expected_overall = PAIR_AMBIGUOUS
        else:
            expected_overall = PAIR_CLEAR
        return value.get("overall") == expected_overall

    def _apply_substantive_assessment(
        self,
        reservation_id: u256,
        item: Reservation,
        book: ExclusivityBook,
        comparison_hash: str,
        result: dict,
    ) -> None:
        item.assessed_at = u256(message_timestamp())
        item.assessed_epoch = u256(int(book.epoch))
        item.comparison_set_hash = comparison_hash
        item.conflict_ids.clear()
        item.ambiguous_ids.clear()
        for incumbent_id in result["conflict_ids"]:
            item.conflict_ids.append(u256(int(incumbent_id)))
        for incumbent_id in result["ambiguous_ids"]:
            item.ambiguous_ids.append(u256(int(incumbent_id)))
        item.consecutive_nondecisions = u32(0)
        item.last_assessment_result = OUTCOME_SUBSTANTIVE

        overall = result["overall"]
        if overall == PAIR_CONFLICT:
            item.status = u8(RES_BLOCKED)
            item.reason = clean_text(
                f"CONFLICT with reservation ids {result['conflict_ids']}",
                MAX_REASON_LEN,
            )
        elif overall == PAIR_AMBIGUOUS:
            item.status = u8(RES_AMBIGUOUS)
            item.reason = clean_text(
                f"AMBIGUOUS against reservation ids {result['ambiguous_ids']}",
                MAX_REASON_LEN,
            )
        else:
            item.status = u8(RES_READY)
            item.reason = "CLEAR: no materially overlapping incumbent reservation"

        ReservationAssessed(
            reservation_id,
            overall,
            epoch=int(book.epoch),
            comparison_set_hash=comparison_hash,
            conflict_ids=[int(v) for v in item.conflict_ids],
            ambiguous_ids=[int(v) for v in item.ambiguous_ids],
        ).emit()

    @gl.public.write
    def assess_reservation(self, reservation_id: u256) -> None:
        item = self._require_reservation(reservation_id)
        if not bool(item.holder_accepted):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: holder has not accepted reservation")
        if int(item.status) in (
            RES_PROPOSED,
            RES_GRANTED,
            RES_RELEASED,
            RES_WITHDRAWN,
            RES_ASSESS_EXHAUSTED,
        ):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation is not assessable")

        book = self._require_book(item.book_id)
        if int(book.status) != BOOK_SEALED or not bool(book.active):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book is not active")
        if str(item.book_hash) != str(book.definition_hash):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation book hash mismatch")
        if str(book.definition_hash) != self._current_book_hash(book):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book definition hash mismatch")
        if str(item.reservation_hash) != self._current_reservation_hash(int(reservation_id), item):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation definition hash mismatch")

        if int(item.assessed_at) != 0 and int(item.assessed_epoch) == int(book.epoch):
            raise gl.vm.UserError(
                f"{ERR_EXPECTED}: reservation already assessed at current book epoch"
            )

        incumbents = self._candidate_incumbents(int(reservation_id), item, book)
        comparison_hash = comparison_set_digest(
            item.reservation_hash,
            int(book.epoch),
            incumbents,
        )

        item.assessment_attempts = u32(int(item.assessment_attempts) + 1)

        # No incumbent reservation can collide. This is intentionally
        # deterministic rather than wasting consensus on an empty comparison.
        if len(incumbents) == 0:
            result = {
                "outcome": OUTCOME_SUBSTANTIVE,
                "comparison_set_hash": comparison_hash,
                "incumbent_ids": [],
                "conflict_ids": [],
                "ambiguous_ids": [],
                "clear_ids": [],
                "overall": PAIR_CLEAR,
            }
            self._apply_substantive_assessment(
                reservation_id,
                item,
                book,
                comparison_hash,
                result,
            )
            return

        expected_ids = [incumbent_id for incumbent_id, _ in incumbents]

        def observe() -> dict:
            return self._observe(
                book,
                int(reservation_id),
                item,
                incumbents,
                comparison_hash,
            )

        def validate(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            leader = leader_result.calldata
            if not isinstance(leader, dict) or "outcome" not in leader:
                return False

            follower = observe()
            if leader.get("outcome") != follower.get("outcome"):
                return False

            if leader.get("outcome") in NON_DECISION_OUTCOMES:
                return True

            if leader.get("outcome") != OUTCOME_SUBSTANTIVE:
                return False
            if not self._substantive_shape_valid(leader, expected_ids, comparison_hash):
                return False
            if not self._substantive_shape_valid(follower, expected_ids, comparison_hash):
                return False

            # Consensus is deliberately strict at the state-consequence
            # boundary: validators must agree on exactly which incumbents
            # conflict and which remain ambiguous. Explanatory relation labels
            # may differ, but they never enter storage or change the outcome.
            if leader["overall"] != follower["overall"]:
                return False
            if [int(v) for v in leader["conflict_ids"]] != [int(v) for v in follower["conflict_ids"]]:
                return False
            if [int(v) for v in leader["ambiguous_ids"]] != [int(v) for v in follower["ambiguous_ids"]]:
                return False
            if [int(v) for v in leader["clear_ids"]] != [int(v) for v in follower["clear_ids"]]:
                return False
            return True

        result = gl.vm.run_nondet_unsafe(observe, validate)
        item.last_assessment_result = str(result.get("outcome", ""))

        if result.get("outcome") == OUTCOME_SUBSTANTIVE:
            self._apply_substantive_assessment(
                reservation_id,
                item,
                book,
                comparison_hash,
                result,
            )
            return

        # A model/infrastructure failure is an explicit non-decision, never
        # an overlap verdict. If this was a stale previous assessment, drop
        # back to ACCEPTED so an old READY result cannot survive a changed book.
        item.status = u8(RES_ACCEPTED)
        item.assessed_at = u256(0)
        item.assessed_epoch = u256(0)
        item.comparison_set_hash = ""
        item.conflict_ids.clear()
        item.ambiguous_ids.clear()
        item.consecutive_nondecisions = u32(int(item.consecutive_nondecisions) + 1)
        item.reason = clean_text(
            f"{result.get('outcome', 'NON_DECISION')}: {result.get('reason', '')}",
            MAX_REASON_LEN,
        )
        if int(item.consecutive_nondecisions) >= MAX_NONDECISION_ATTEMPTS:
            item.status = u8(RES_ASSESS_EXHAUSTED)
            ReservationAssessmentExhausted(
                item.consecutive_nondecisions,
                reservation_id,
            ).emit()
        else:
            ReservationAssessmentNonDecision(
                str(result.get("outcome", "")),
                reservation_id,
                attempt=int(item.consecutive_nondecisions),
            ).emit()

    @gl.public.write
    def finalize_grant(self, reservation_id: u256) -> None:
        item = self._require_reservation(reservation_id)
        if int(item.status) != RES_READY:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation is not READY")
        book = self._require_book(item.book_id)
        self._require_owner(book)
        if str(book.definition_hash) != self._current_book_hash(book):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book definition hash mismatch")
        if str(item.book_hash) != str(book.definition_hash):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation book hash mismatch")
        if str(item.reservation_hash) != self._current_reservation_hash(
            int(reservation_id), item
        ):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation definition hash mismatch")
        if not bool(book.active) or int(book.status) != BOOK_SEALED:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book is not active")
        if int(item.assessed_epoch) != int(book.epoch):
            raise gl.vm.UserError(
                f"{ERR_EXPECTED}: assessment is stale; book epoch changed"
            )

        incumbents = self._candidate_incumbents(int(reservation_id), item, book)
        expected_hash = comparison_set_digest(
            item.reservation_hash,
            int(book.epoch),
            incumbents,
        )
        if str(item.comparison_set_hash) != expected_hash:
            raise gl.vm.UserError(
                f"{ERR_EXPECTED}: assessment comparison set is stale"
            )
        if len(item.conflict_ids) != 0 or len(item.ambiguous_ids) != 0:
            raise gl.vm.UserError(
                f"{ERR_EXPECTED}: unresolved exclusivity conflict"
            )

        item.status = u8(RES_GRANTED)
        item.granted_at = u256(message_timestamp())
        book.epoch = u256(int(book.epoch) + 1)
        ReservationGranted(
            item.holder,
            reservation_id,
            reservation_hash=item.reservation_hash,
            book_epoch=int(book.epoch),
        ).emit()

    @gl.public.write
    def release_reservation(self, reservation_id: u256) -> None:
        item = self._require_reservation(reservation_id)
        if int(item.status) != RES_GRANTED:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation is not granted")
        if str(item.holder).lower() != str(gl.message.sender_address).lower():
            raise gl.vm.UserError(f"{ERR_EXPECTED}: only holder may release exclusivity")
        book = self._require_book(item.book_id)
        if str(book.definition_hash) != self._current_book_hash(book):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: book definition hash mismatch")
        if str(item.book_hash) != str(book.definition_hash):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation book hash mismatch")
        if str(item.reservation_hash) != self._current_reservation_hash(
            int(reservation_id), item
        ):
            raise gl.vm.UserError(f"{ERR_EXPECTED}: reservation definition hash mismatch")
        item.status = u8(RES_RELEASED)
        item.released_at = u256(message_timestamp())
        book.epoch = u256(int(book.epoch) + 1)
        ReservationReleased(
            item.holder,
            reservation_id,
            book_epoch=int(book.epoch),
        ).emit()

    # ------------------------------------------------------------------
    # Views / composability
    # ------------------------------------------------------------------

    @gl.public.view
    def get_book(self, book_id: u256) -> dict:
        book = self._require_book(book_id)
        return {
            "owner": str(book.owner),
            "name": str(book.name),
            "domain_key": str(book.domain_key),
            "semantic_charter": str(book.semantic_charter),
            "status": int(book.status),
            "sealed": int(book.status) == BOOK_SEALED,
            "active": bool(book.active),
            "definition_hash": str(book.definition_hash),
            "epoch": int(book.epoch),
            "reservation_ids": [int(v) for v in book.reservation_ids],
        }

    @gl.public.view
    def get_reservation(self, reservation_id: u256) -> dict:
        item = self._require_reservation(reservation_id)
        return {
            "book_id": int(item.book_id),
            "book_hash": str(item.book_hash),
            "grantor": str(item.grantor),
            "holder": str(item.holder),
            "right_scope": str(item.right_scope),
            "product_scope": str(item.product_scope),
            "territory_scope": str(item.territory_scope),
            "channel_scope": str(item.channel_scope),
            "audience_scope": str(item.audience_scope),
            "start_at": int(item.start_at),
            "end_at": int(item.end_at),
            "reservation_hash": str(item.reservation_hash),
            "status": int(item.status),
            "status_name": STATUS_NAMES.get(int(item.status), "UNKNOWN"),
            "holder_accepted": bool(item.holder_accepted),
            "created_at": int(item.created_at),
            "assessed_at": int(item.assessed_at),
            "assessed_epoch": int(item.assessed_epoch),
            "comparison_set_hash": str(item.comparison_set_hash),
            "conflict_ids": [int(v) for v in item.conflict_ids],
            "ambiguous_ids": [int(v) for v in item.ambiguous_ids],
            "assessment_attempts": int(item.assessment_attempts),
            "consecutive_nondecisions": int(item.consecutive_nondecisions),
            "last_assessment_result": str(item.last_assessment_result),
            "reason": str(item.reason),
            "granted_at": int(item.granted_at),
            "released_at": int(item.released_at),
        }

    @gl.public.view
    def is_granted(
        self,
        reservation_id: u256,
        expected_reservation_hash: str,
        expected_book_hash: str,
    ) -> bool:
        if reservation_id not in self.reservations:
            return False
        item = self.reservations[reservation_id]
        if int(item.status) != RES_GRANTED:
            return False
        if str(item.reservation_hash).lower() != str(expected_reservation_hash).strip().lower():
            return False
        if str(item.book_hash).lower() != str(expected_book_hash).strip().lower():
            return False
        if item.book_id not in self.books:
            return False
        book = self.books[item.book_id]
        if str(book.definition_hash).lower() != str(item.book_hash).lower():
            return False
        if str(book.definition_hash) != self._current_book_hash(book):
            return False
        if str(item.reservation_hash) != self._current_reservation_hash(
            int(reservation_id), item
        ):
            return False
        return True

    @gl.public.view
    def get_protocol_dictionary(self) -> dict:
        return {
            "protocol": PROTOCOL_VERSION,
            "relations": list(ALLOWED_RELATIONS),
            "dimensions": list(DIMENSIONS),
            "pair_rule": (
                "CLEAR if any dimension DISJOINT; else AMBIGUOUS if any "
                "dimension AMBIGUOUS; else CONFLICT"
            ),
            "interval_rule": "half-open [start_at,end_at)",
            "max_reservations_per_book": MAX_RESERVATIONS_PER_BOOK,
            "max_comparison_set": MAX_COMPARISON_SET,
            "max_nondecision_attempts": MAX_NONDECISION_ATTEMPTS,
            "trust_boundary": (
                "SOLE prevents overlapping grants inside the canonical book; "
                "it is not a legal opinion and consumers must bind the intended "
                "SOLE deployment, book id and book hash"
            ),
        }
