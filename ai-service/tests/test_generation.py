"""Pure-logic tests for the generation pipeline — no models, no network.

These import only the light prompt/query helpers (torch is lazy-loaded), so they
run in CI without the ML stack.
"""
from collections import namedtuple

from app.inference import generator as g
from app.inference import remote as r

# Minimal stand-in for a retrieved chunk (title/text/score are what the prompt uses).
Chunk = namedtuple("Chunk", "title text score source url", defaults=(0.0, "", ""))


def test_retrieval_query_passthrough_without_history():
    assert g.retrieval_query("what is a hash table", []) == "what is a hash table"


def test_retrieval_query_anchors_on_running_topic():
    # The follow-up has no topic of its own; the anchor must reinstate it.
    history = [
        {"role": "user", "content": "Explain how B-trees stay balanced"},
        {"role": "assistant", "content": "A B-tree splits a node when it overflows."},
        {"role": "user", "content": "can you explain in more detail"},
    ]
    q = g.retrieval_query("show me the code", history)
    assert "B-tree" in q
    assert "show me the code" in q


def test_format_history_labels_and_truncates():
    history = [{"role": "user", "content": "x" * 1000}, {"role": "assistant", "content": "ok"}]
    out = g._format_history(history, max_chars=50)
    assert out.startswith("User: ")
    assert "Tutor: ok" in out
    assert "…" in out  # long content truncated


def test_build_messages_shape():
    history = [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}]
    chunks = [Chunk(title="B-tree", text="info", score=9.0)]
    msgs = g.build_messages("q2", chunks, history)
    assert msgs[0]["role"] == "system"
    assert [m["role"] for m in msgs[1:]] == ["user", "assistant", "user"]
    assert "Context:" in msgs[-1]["content"]
    assert "q2" in msgs[-1]["content"]


def test_context_block_flags_thin_retrieval():
    context, note = g._context_block([])
    assert context == "(no relevant context retrieved)"
    assert note.strip()  # a low-confidence note is added


def test_iter_sse_deltas_yields_content_and_stops_on_done():
    lines = [
        b'data: {"choices":[{"delta":{"content":"Hel"}}]}',
        b': heartbeat comment',
        b'data: {"choices":[{"delta":{"content":"lo"}}]}',
        b'data: {"choices":[{"delta":{}}]}',
        b'data: [DONE]',
        b'data: {"choices":[{"delta":{"content":"ignored"}}]}',
    ]
    assert list(r.iter_sse_deltas(lines)) == ["Hel", "lo"]


def test_iter_sse_deltas_skips_malformed_lines():
    lines = [
        b"data: not-json",
        b'data: {"choices":[]}',
        b'data: {"choices":[{"delta":{"content":"ok"}}]}',
    ]
    assert list(r.iter_sse_deltas(lines)) == ["ok"]
