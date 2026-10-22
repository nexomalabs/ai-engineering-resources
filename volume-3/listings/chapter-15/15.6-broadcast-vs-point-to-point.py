# Applied AI Engineering, Volume III, Chapter 15
# Section 15.6, Broadcast vs. Point-to-Point
# Copied from the book by scripts/export_listings.py. Report errors as errata.

class AgentBus:
    """Simple publish-subscribe bus supporting both P2P and broadcast messaging."""

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}

    def register(self, agent_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[agent_id] = q
        return q

    def inbox(self, agent_id: str) -> asyncio.Queue:
        """The queue a registered agent reads its messages from."""
        return self._queues[agent_id]

    async def send(self, msg: MessageEnvelope) -> None:
        """Point-to-point send."""
        if msg.recipient_id in self._queues:
            await self._queues[msg.recipient_id].put(msg)
        else:
            raise KeyError(f"Unknown recipient: {msg.recipient_id}")

    async def broadcast(self, msg: MessageEnvelope) -> None:
        """Send to all registered agents except the sender."""
        for agent_id, q in self._queues.items():
            if agent_id != msg.sender_id:
                broadcast_copy = MessageEnvelope(**{
                    **asdict(msg),
                    "recipient_id": agent_id,
                    "message_id": str(uuid.uuid4()),
                })
                await q.put(broadcast_copy)
