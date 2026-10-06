import asyncio
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class HelloState(TypedDict):
    name: str
    greeting: str


def greet_node(state: HelloState) -> dict:
    return {"greeting": f"Hello, {state['name']}!"}


def shout_node(state: HelloState) -> dict:
    return {"greeting": state["greeting"].upper()}


builder = StateGraph(HelloState)
builder.add_node("greet", greet_node)
builder.add_node("shout", shout_node)
builder.add_edge(START, "greet")
builder.add_edge("greet", "shout")
builder.add_edge("shout", END)

graph = builder.compile()


async def main():
    result = await graph.ainvoke({"name": "Nikhil"})
    print(result)


if __name__ == "__main__":
    asyncio.run(main())