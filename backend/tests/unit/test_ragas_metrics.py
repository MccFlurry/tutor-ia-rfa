import pytest
from scripts import ragas_metrics as rm


class FakeLLM:
    """Devuelve respuestas .content predefinidas, en orden, por cada ainvoke."""
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    async def ainvoke(self, messages):
        resp = self._responses[self.calls]
        self.calls += 1
        class _M:
            content = resp
        return _M()


class FakeEmbedder:
    def __init__(self, vectors):
        self._vectors = vectors

    async def aembed_documents(self, texts):
        return self._vectors[: len(texts)]


@pytest.mark.asyncio
async def test_faithfulness_half_supported():
    judge = FakeLLM([
        '{"claims": ["c1", "c2"]}',
        '{"verdicts": [{"claim": "c1", "supported": true}, {"claim": "c2", "supported": false}]}',
    ])
    score = await rm.metric_faithfulness(judge, "answer", ["ctx"])
    assert score == 0.5


@pytest.mark.asyncio
async def test_context_recall_all_attributable():
    judge = FakeLLM([
        '{"sentences": ["s1", "s2"]}',
        '{"verdicts": [{"sentence": "s1", "attributable": true}, {"sentence": "s2", "attributable": true}]}',
    ])
    score = await rm.metric_context_recall(judge, "ground truth", ["ctx"])
    assert score == 1.0


@pytest.mark.asyncio
async def test_context_precision_top_ranked_relevant():
    judge = FakeLLM([
        '{"verdicts": [{"useful": true}, {"useful": false}]}',
    ])
    score = await rm.metric_context_precision(judge, "q", "gt", ["c1", "c2"])
    assert score == 1.0


@pytest.mark.asyncio
async def test_context_entities_recall_half_present():
    judge = FakeLLM([
        '{"entities": ["Retrofit", "Coroutine"]}',
        '{"verdicts": [{"entity": "Retrofit", "present": true}, {"entity": "Coroutine", "present": false}]}',
    ])
    score = await rm.metric_context_entities_recall(judge, "ground truth", ["ctx"])
    assert score == 0.5


@pytest.mark.asyncio
async def test_context_entities_recall_no_entities_returns_one():
    judge = FakeLLM(['{"entities": []}'])
    score = await rm.metric_context_entities_recall(judge, "ground truth", ["ctx"])
    assert score == 1.0


@pytest.mark.asyncio
async def test_answer_correctness_perfect():
    # tp=2, fp=0, fn=0 → F1=1.0 ; embeddings idénticos → coseno=1.0 → 0.75+0.25=1.0
    judge = FakeLLM(['{"tp": 2, "fp": 0, "fn": 0}'])
    embedder = FakeEmbedder([[1.0, 0.0], [1.0, 0.0]])
    score = await rm.metric_answer_correctness(judge, embedder, "answer", "ground truth")
    assert score == 1.0


@pytest.mark.asyncio
async def test_answer_correctness_partial():
    # tp=1, fp=1, fn=1 → F1 = 1/(1+0.5*2)=0.5 ; coseno=0 → 0.75*0.5 = 0.375
    judge = FakeLLM(['{"tp": 1, "fp": 1, "fn": 1}'])
    embedder = FakeEmbedder([[1.0, 0.0], [0.0, 1.0]])
    score = await rm.metric_answer_correctness(judge, embedder, "answer", "ground truth")
    assert score == 0.375
