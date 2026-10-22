# Applied AI Engineering, Volume III, Chapter 15
# Section 15.9, Communication Failures
# Copied from the book by scripts/export_listings.py. Report errors as errata.

async def heartbeat_monitor(bus: AgentBus, agent_ids: list[str],
                            interval: float = 10.0,
                            timeout: float = 30.0) -> None:
    """Agents send heartbeat messages to "monitor"; report any that fall silent."""
    inbox = bus.register("monitor")
    loop = asyncio.get_running_loop()
    last_seen: dict[str, float] = {aid: loop.time() for aid in agent_ids}
    reported: set[str] = set()
    while True:
        try:
            msg = await asyncio.wait_for(inbox.get(), timeout=interval)
            if msg.message_type == "heartbeat":
                last_seen[msg.sender_id] = loop.time()
        except asyncio.TimeoutError:
            pass  # no message this interval; check for silent agents below
        now = loop.time()
        for agent_id in agent_ids:
            if agent_id not in reported and now - last_seen[agent_id] > timeout:
                reported.add(agent_id)
                print(f"[MONITOR] Agent {agent_id} appears to have failed.")
                # In production: trigger recovery, reassign tasks, alert operator
