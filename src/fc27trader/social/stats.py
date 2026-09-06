from __future__ import annotations

from statistics import mean, median
from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import PublicPrediction


def public_prediction_stats(session: Session) -> dict:
    rows = list(session.scalars(select(PublicPrediction).where(PublicPrediction.status.in_(["published", "resolved"]))))
    resolved = [r for r in rows if (r.result_json or {}).get("resolved")]
    if not resolved:
        return {"sample_size": 0, "accuracy": None, "profitable_after_tax_rate": None, "mean_return": None, "median_return": None, "mean_alpha": None, "recent_performance": None}
    results = [r.result_json for r in resolved]
    returns = [float(x["return_pct"]) for x in results if x.get("return_pct") is not None]
    alphas = [float(x["alpha_pct"]) for x in results if x.get("alpha_pct") is not None]
    accuracy_rows = [bool(x["directional_correct"]) for x in results if x.get("directional_correct") is not None]
    profitable_rows = [bool(x["profitable_after_tax"]) for x in results if x.get("profitable_after_tax") is not None]
    return {
        "sample_size": len(resolved),
        "accuracy": sum(accuracy_rows) / len(accuracy_rows) if accuracy_rows else None,
        "profitable_after_tax_rate": sum(profitable_rows) / len(profitable_rows) if profitable_rows else None,
        "mean_return": mean(returns) if returns else None,
        "median_return": median(returns) if returns else None,
        "mean_alpha": mean(alphas) if alphas else None,
    }
