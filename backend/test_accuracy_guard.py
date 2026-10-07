"""Deterministic test of the price/product accuracy guard (no API calls).

Run from backend/:  python test_accuracy_guard.py
"""

import asyncio

from pydantic_ai.messages import ModelResponse, RetryPromptPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

import agent
from models import PageContext


def deps():
    return agent.build_deps(None, PageContext())


async def main():
    # 1) Model invents $65.00 -> guard rejects -> model looks it up -> quotes real $68.00.
    calls = []

    def hallucinate_then_fix(messages, info: AgentInfo):
        calls.append(1)
        out = info.output_tools[0].name
        if len(calls) == 1:
            return ModelResponse(parts=[ToolCallPart(out, {"reply": "The Basic Hoodie Big Yale is $65.00.", "product_ids": ["basic-hoodie-big-yale"]})])
        if len(calls) == 2:
            retry = [p for m in messages for p in m.parts if isinstance(p, RetryPromptPart)]
            print("1) guard feedback:", retry[-1].content)
            return ModelResponse(parts=[ToolCallPart("get_product_details", {"product": "basic-hoodie-big-yale"})])
        return ModelResponse(parts=[ToolCallPart(out, {"reply": "The Basic Hoodie Big Yale is $68.00.", "product_ids": ["basic-hoodie-big-yale"]})])

    with agent.shop_agent.override(model=FunctionModel(hallucinate_then_fix)):
        r = await agent.run_chat("how much is the basic hoodie big yale?", [], deps())
    assert r.reply.endswith("$68.00."), r.reply
    print("   final reply:", r.reply)

    # 2) Model never fixes it -> shopper gets an honest fallback, never the wrong price.
    def always_wrong(messages, info):
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {"reply": "Only $12.99 today!", "product_ids": ["fake-id"]})])

    with agent.shop_agent.override(model=FunctionModel(always_wrong)):
        r = await agent.run_chat("price?", [], deps())
    assert r.reply == agent.FALLBACK_REPLY and "$12.99" not in r.reply
    print("2) always-wrong model ->", r.reply)

    # 3) The shopper's own budget is allowed.
    before = agent.STATS["guard_corrections"]

    def budget(messages, info):
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {"reply": "Here are some gifts under $50!", "product_ids": []})])

    with agent.shop_agent.override(model=FunctionModel(budget)):
        r = await agent.run_chat("Gifts under $50", [], deps())
    assert agent.STATS["guard_corrections"] == before
    print("3) shopper budget ->", r.reply)
    print("ALL PASS", {k: agent.STATS[k] for k in ("guard_checks", "guard_corrections", "guard_fallbacks")})


if __name__ == "__main__":
    asyncio.run(main())
