"""Step 6: every place chat text is stored, and erasing one customer from all of them.

The chapter's opening story: a customer typed her passport number and date of birth into
the chat. Months later she asked for her data to be erased, and copies turned up in the
conversation log, the debugging log, the semantic cache, the vector store behind Wren's
memory and the nightly backup, while the erasure procedure checked only the main database,
which never held chat text at all. The fix had two parts: redact personal data before
anything stores it, and keep a register of every store that holds chat text, with a user
identifier on every record, so that an erasure reaches all of them.

    python solution/chat_store.py
"""

from dataclasses import dataclass, field

from pii_regex import redact_with_regex_fallback

# Every store that receives chat text: the register the erasure procedure works from.
CHAT_STORES = [
    "conversation log",
    "debugging log",
    "semantic cache",
    "memory vector store",
    "nightly backup",
]


@dataclass
class Store:
    name: str
    records: list[dict] = field(default_factory=list)  # each {"user_id": ..., "text": ...}

    def write(self, user_id: str, text: str) -> None:
        self.records.append({"user_id": user_id, "text": text})

    def erase(self, user_id: str) -> int:
        """Delete the user's records; return how many there were."""
        kept = [r for r in self.records if r["user_id"] != user_id]
        removed = len(self.records) - len(kept)
        self.records = kept
        return removed

    def copies_of(self, value: str) -> int:
        return sum(value in r["text"] for r in self.records)


class ChatPlatform:
    def __init__(self, redact_on_ingest: bool):
        self.redact_on_ingest = redact_on_ingest
        self.stores = {name: Store(name) for name in CHAT_STORES}
        self.main_database = Store("main database")  # orders and accounts, never chat text

    def receive(self, user_id: str, message: str) -> str:
        """Take a chat message in. Every chat store gets a copy, as in production."""
        text = redact_with_regex_fallback(message)[0] if self.redact_on_ingest else message
        for store in self.stores.values():
            store.write(user_id, text)
        return text

    def erase_from_main_database(self, user_id: str) -> int:
        """The erasure procedure as it was: it checked the one store it knew about."""
        return self.main_database.erase(user_id)

    def erase_everywhere(self, user_id: str) -> dict[str, int]:
        """The erasure procedure after the fix: every store in the register."""
        return {name: store.erase(user_id) for name, store in self.stores.items()}

    def copies_of(self, value: str) -> dict[str, int]:
        found = {name: store.copies_of(value) for name, store in self.stores.items()}
        return {name: n for name, n in found.items() if n}


PASSPORT = "123456789"
MESSAGE = (
    f"To prove who I am: my passport number is {PASSPORT} and my date of birth is "
    "14/03/1987. Where is my parcel?"
)


def main() -> None:
    for label, redact in (("Before the fix", False), ("After the fix", True)):
        platform = ChatPlatform(redact_on_ingest=redact)
        stored = platform.receive("cust-2291", MESSAGE)
        platform.receive("cust-4410", "Can you change my delivery slot to Friday?")
        print(f"=== {label} ===")
        print(f"Stored text   : {stored}")
        print(f"Passport copies: {platform.copies_of(PASSPORT) or 'none'}")
        if redact:
            erased = platform.erase_everywhere("cust-2291")
            print(
                f"Erasure       : removed {sum(erased.values())} records from {len(erased)} stores"
            )
        else:
            erased = platform.erase_from_main_database("cust-2291")
            print(f"Erasure       : removed {erased} records from the main database")
        remaining = sum(
            r["user_id"] == "cust-2291" for s in platform.stores.values() for r in s.records
        )
        print(f"Records of cust-2291 left: {remaining}\n")


if __name__ == "__main__":
    main()
