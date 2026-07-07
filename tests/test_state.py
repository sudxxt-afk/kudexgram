from kudexgram import MemoryStateStore


async def test_memory_state_store_lifecycle() -> None:
    store = MemoryStateStore()

    await store.set("chat:1", {"step": "name"})
    assert await store.get("chat:1") == {"step": "name"}

    await store.clear("chat:1")
    assert await store.get("chat:1") is None


async def test_memory_state_store_versions_records() -> None:
    store = MemoryStateStore()

    await store.save("chat:1", {"step": "name"})
    first = await store.load("chat:1")
    await store.save("chat:1", {"step": "age"})
    second = await store.load("chat:1")

    assert first is not None
    assert second is not None
    assert first.version == 1
    assert second.version == 2
    assert second.value == {"step": "age"}


async def test_memory_state_store_expires_records() -> None:
    store = MemoryStateStore()

    await store.save("chat:1", {"step": "name"}, ttl_seconds=0)

    assert await store.load("chat:1") is None
