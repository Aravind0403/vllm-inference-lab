#!/usr/bin/env python3
"""
nano_vllm.py - A Zero-Dependency Minimalist Continuous Batching & PagedAttention Engine
Inspired by vLLM v1 and infra.bea.ai inference systems guides.

Run with:
    python3 nano_vllm.py
"""

import collections
import time
from typing import Dict, List, Optional, Tuple

BLOCK_SIZE = 16  # 16 tokens per physical block


class PhysicalBlock:
    def __init__(self, block_id: int):
        self.block_id = block_id
        self.ref_count = 0
        self.block_hash: Optional[int] = None
        self.token_ids: List[int] = []

    def __repr__(self):
        return f"[Block {self.block_id}: ref={self.ref_count}, tokens={len(self.token_ids)}]"


class BlockPool:
    """Manages physical GPU memory blocks, reference counts, and LRU eviction."""

    def __init__(self, num_blocks: int = 16):
        self.num_blocks = num_blocks
        self.blocks = [PhysicalBlock(i) for i in range(num_blocks)]
        # ref_count == 0 blocks reside in free_block_queue (LRU order)
        self.free_block_queue: collections.deque[int] = collections.deque(range(num_blocks))
        # Hash lookup table for instant O(1) prefix cache hits
        self.cached_hash_to_block: Dict[int, int] = {}

    def get_num_free_blocks(self) -> int:
        return len(self.free_block_queue)

    def allocate_block(self, block_hash: Optional[int] = None) -> int:
        # Check if block is already cached (Prefix Cache Hit)
        if block_hash is not None and block_hash in self.cached_hash_to_block:
            block_id = self.cached_hash_to_block[block_hash]
            block = self.blocks[block_id]
            if block.ref_count == 0:
                # Resurrect from LRU eviction queue!
                self.free_block_queue.remove(block_id)
            block.ref_count += 1
            return block_id

        # Allocate new physical block from LRU
        if not self.free_block_queue:
            raise MemoryError("Out of KV Cache physical blocks! Preemption required.")

        block_id = self.free_block_queue.popleft()
        block = self.blocks[block_id]

        # If evicted block had an old hash, invalidate old cache entry
        if block.block_hash in self.cached_hash_to_block and self.cached_hash_to_block[block.block_hash] == block_id:
            del self.cached_hash_to_block[block.block_hash]

        block.ref_count = 1
        block.block_hash = block_hash
        block.token_ids = []

        if block_hash is not None:
            self.cached_hash_to_block[block_hash] = block_id

        return block_id

    def free_block(self, block_id: int):
        block = self.blocks[block_id]
        block.ref_count -= 1
        if block.ref_count == 0:
            # Moves to tail of LRU queue; REMAINS searchable in cached_hash_to_block!
            self.free_block_queue.append(block_id)


class Request:
    def __init__(self, req_id: str, prompt_tokens: List[int], max_tokens: int):
        self.req_id = req_id
        self.prompt_tokens = prompt_tokens
        self.output_tokens: List[int] = []
        self.max_tokens = max_tokens
        self.block_table: List[int] = []
        self.num_computed_tokens = 0

    @property
    def total_tokens(self) -> int:
        return len(self.prompt_tokens) + len(self.output_tokens)

    @property
    def is_finished(self) -> bool:
        return len(self.output_tokens) >= self.max_tokens

    def get_num_uncomputed_tokens(self) -> int:
        return self.total_tokens - self.num_computed_tokens


class NanoScheduler:
    """Continuous Batching Scheduler enforcing vLLM v1's Unified Scheduling Invariant."""

    def __init__(self, block_pool: BlockPool, max_batched_tokens: int = 32, max_seqs: int = 4):
        self.block_pool = block_pool
        self.max_batched_tokens = max_batched_tokens
        self.max_seqs = max_seqs

        # 3-tier queue hierarchy (PR #58947)
        self.running: List[Request] = []
        self.kv_holding_waiting: collections.deque[Request] = collections.deque()
        self.waiting: collections.deque[Request] = collections.deque()

    def add_request(self, req: Request):
        self.waiting.append(req)

    def schedule_step(self) -> Tuple[List[Tuple[Request, int]], List[Request]]:
        """Unified step: advances N_computed -> N_target."""
        scheduled: List[Tuple[Request, int]] = []
        finished: List[Request] = []

        remaining_tokens = self.max_batched_tokens
        remaining_seqs = self.max_seqs

        # Phase 1: Schedule RUNNING requests first (protect TPOT latency!)
        next_running: List[Request] = []
        for req in self.running:
            if remaining_seqs <= 0 or remaining_tokens <= 0:
                # Preempt to holding queue
                self.kv_holding_waiting.append(req)
                continue

            # In decode phase, request asks for 1 token
            blocks_needed = (req.total_tokens + 1 + BLOCK_SIZE - 1) // BLOCK_SIZE
            current_blocks = len(req.block_table)

            if blocks_needed > current_blocks:
                if self.block_pool.get_num_free_blocks() == 0:
                    # Memory exhausted -> pause to holding queue
                    self.kv_holding_waiting.append(req)
                    continue
                new_block = self.block_pool.allocate_block()
                req.block_table.append(new_block)

            scheduled.append((req, 1))
            remaining_tokens -= 1
            remaining_seqs -= 1
            next_running.append(req)

        self.running = next_running

        # Phase 2: Drain kv_holding_waiting before fresh waiting requests (PR #58947)
        while self.kv_holding_waiting and remaining_seqs > 0 and remaining_tokens > 0:
            req = self.kv_holding_waiting.popleft()
            scheduled.append((req, 1))
            remaining_tokens -= 1
            remaining_seqs -= 1
            self.running.append(req)

        # Phase 3: Admit WAITING requests with dynamic chunked prefill
        while self.waiting and remaining_seqs > 0 and remaining_tokens > 0:
            req = self.waiting[0]
            uncomputed = req.get_num_uncomputed_tokens()
            chunk = min(uncomputed, remaining_tokens)

            # Check if block allocation possible
            blocks_needed = (req.num_computed_tokens + chunk + BLOCK_SIZE - 1) // BLOCK_SIZE
            current_blocks = len(req.block_table)
            delta_blocks = blocks_needed - current_blocks

            if delta_blocks > self.block_pool.get_num_free_blocks():
                break  # Not enough memory blocks; wait for subsequent steps

            self.waiting.popleft()
            for _ in range(delta_blocks):
                # Simple prefix hash simulation
                h = hash(tuple(req.prompt_tokens[: len(req.block_table) * BLOCK_SIZE + BLOCK_SIZE]))
                block_id = self.block_pool.allocate_block(block_hash=h)
                req.block_table.append(block_id)

            scheduled.append((req, chunk))
            remaining_tokens -= chunk
            remaining_seqs -= 1
            self.running.append(req)

        # Simulate execution
        for req, tokens_run in scheduled:
            req.num_computed_tokens += tokens_run
            if req.num_computed_tokens >= len(req.prompt_tokens):
                # Generate a dummy token
                dummy_token = 1000 + len(req.output_tokens)
                req.output_tokens.append(dummy_token)

            if req.is_finished:
                # Free blocks back to pool
                for b_id in req.block_table:
                    self.block_pool.free_block(b_id)
                self.running.remove(req)
                finished.append(req)

        return scheduled, finished


def run_demo():
    print("=" * 70)
    print("nano-vllm: Minimalist Continuous Batching & PagedAttention Engine")
    print("=" * 70)

    pool = BlockPool(num_blocks=12)
    scheduler = NanoScheduler(pool, max_batched_tokens=24, max_seqs=3)

    # Common system prompt (tokens 1..16 -> exactly 1 block)
    system_prompt = list(range(1, 17))
    req1 = Request("Req-1 (Chat-A)", system_prompt + [101, 102], max_tokens=3)
    req2 = Request("Req-2 (Chat-B [Shared Prefix])", system_prompt + [201, 202], max_tokens=2)
    req3 = Request("Req-3 (Long Prompt)", list(range(300, 328)), max_tokens=2)

    scheduler.add_request(req1)
    scheduler.add_request(req2)
    scheduler.add_request(req3)

    step = 0
    while scheduler.running or scheduler.waiting or scheduler.kv_holding_waiting:
        step += 1
        print(f"\n--- STEP {step} ---")
        scheduled, finished = scheduler.schedule_step()

        print(f"Active Free Blocks: {pool.get_num_free_blocks()} / {pool.num_blocks}")
        print(f"Scheduled ({len(scheduled)}):")
        for req, t_count in scheduled:
            phase = "Prefill Chunk" if req.num_computed_tokens < len(req.prompt_tokens) else "Decode (1 tok)"
            print(f"  * {req.req_id:28} | Phase: {phase:15} | Tokens Run: {t_count:2} | Blocks: {req.block_table}")

        if finished:
            print("Finished:")
            for req in finished:
                print(f"  ✓ {req.req_id} completed {len(req.output_tokens)} tokens! (Blocks freed to LRU)")

    print("\n" + "=" * 70)
    print("All requests completed successfully!")
    print(f"Cached prefix hashes remaining in BlockPool: {len(pool.cached_hash_to_block)}")
    print(f"All physical blocks safely returned to LRU: {pool.get_num_free_blocks() == pool.num_blocks}")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
