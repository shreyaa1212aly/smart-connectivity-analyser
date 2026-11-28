from fastapi import HTTPException

import backend.main as main


PREDICTION = {"success": True, "predicted_connectivity_score": 82.5}
ANOMALY = {"success": True, "anomaly": False}


def test_combined_ai_analysis_returns_both_results(client, monkeypatch):
    monkeypatch.setattr(main, "ai_prediction", lambda: PREDICTION)
    monkeypatch.setattr(main, "ai_anomaly", lambda: ANOMALY)

    response = client.get("/api/ai/analyze")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "available": True,
        "status": "success",
        "prediction": PREDICTION,
        "anomaly": ANOMALY,
        "errors": {},
    }


def test_combined_ai_analysis_preserves_anomaly_when_prediction_fails(
    client, monkeypatch
):
    def fail_prediction():
        raise HTTPException(status_code=503, detail="model path is private")

    monkeypatch.setattr(main, "ai_prediction", fail_prediction)
    monkeypatch.setattr(main, "ai_anomaly", lambda: ANOMALY)

    response = client.get("/api/ai/analyze")

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["available"] is True
    assert response.json()["status"] == "partial"
    assert response.json()["prediction"] is None
    assert response.json()["anomaly"] == ANOMALY
    assert response.json()["errors"]["prediction"] == {
        "status_code": 503,
        "message": "AI component is unavailable.",
    }
    assert "private" not in response.text


def test_combined_ai_analysis_preserves_prediction_when_anomaly_fails(
    client, monkeypatch
):
    monkeypatch.setattr(main, "ai_prediction", lambda: PREDICTION)
    monkeypatch.setattr(
        main,
        "ai_anomaly",
        lambda: (_ for _ in ()).throw(HTTPException(status_code=503)),
    )

    response = client.get("/api/ai/analyze")

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["available"] is True
    assert response.json()["status"] == "partial"
    assert response.json()["prediction"] == PREDICTION
    assert response.json()["anomaly"] is None
    assert response.json()["errors"]["anomaly"] == {
        "status_code": 503,
        "message": "AI component is unavailable.",
    }


def test_combined_ai_analysis_reports_structured_total_failure(
    client, monkeypatch
):
    def fail_prediction():
        raise RuntimeError("sensitive implementation detail")

    def fail_anomaly():
        raise HTTPException(status_code=400, detail="private input details")

    monkeypatch.setattr(main, "ai_prediction", fail_prediction)
    monkeypatch.setattr(main, "ai_anomaly", fail_anomaly)

    response = client.get("/api/ai/analyze")

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["available"] is False
    assert response.json()["status"] == "error"
    assert response.json()["prediction"] is None
    assert response.json()["anomaly"] is None
    assert set(response.json()["errors"]) == {"prediction", "anomaly"}
    assert "sensitive" not in response.text
    assert "private" not in response.text
