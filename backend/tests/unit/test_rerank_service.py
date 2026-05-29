from app.services import rerank_service


class FakeCE:
    def __init__(self, scores):
        self._scores = scores

    def predict(self, pairs):
        return self._scores[: len(pairs)]


def test_rerank_orders_by_score_and_truncates():
    cands = [{"content": "a"}, {"content": "b"}, {"content": "c"}]
    ranked = rerank_service.rerank("q", cands, top_k=2, model=FakeCE([0.1, 0.9, 0.5]))
    assert [c["content"] for c in ranked] == ["b", "c"]
    assert ranked[0]["rerank_score"] == 0.9


def test_rerank_empty_candidates():
    assert rerank_service.rerank("q", [], top_k=5, model=FakeCE([])) == []


def test_rerank_fallback_when_model_unavailable(monkeypatch):
    monkeypatch.setattr(rerank_service, "_get_model", lambda: None)
    cands = [{"content": "a"}, {"content": "b"}, {"content": "c"}]
    ranked = rerank_service.rerank("q", cands, top_k=2)
    assert [c["content"] for c in ranked] == ["a", "b"]
