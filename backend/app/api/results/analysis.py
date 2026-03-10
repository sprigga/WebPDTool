"""
Report Analysis Endpoint

Provides descriptive statistics (mean, median, std dev, MAD) for:
1. Per-test-item execution_duration_ms across sessions matching filters
2. Total session duration (test_duration_seconds) across matched sessions

Groups by test_plan_name (script name) rather than individual test_plan_id rows.
"""

import statistics
from collections import defaultdict
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel
from app.models.testplan import TestPlan as TestPlanModel

router = APIRouter()


def _compute_stats(data: List[float]) -> dict:
    """Compute mean, median, stdev, MAD for a list of floats."""
    if not data:
        return {"sample_count": 0, "mean": None, "median": None, "stdev": None, "mad": None}
    n = len(data)
    mean = statistics.mean(data)
    median = statistics.median(data)
    stdev = statistics.stdev(data) if n >= 2 else 0.0
    mad = sum(abs(x - mean) for x in data) / n
    return {
        "sample_count": n,
        "mean": round(mean, 3),
        "median": round(median, 3),
        "stdev": round(stdev, 3),
        "mad": round(mad, 3),
    }


class ItemStats(BaseModel):
    item_no: int
    item_name: str
    sample_count: int
    mean_ms: Optional[float]
    median_ms: Optional[float]
    stdev_ms: Optional[float]
    mad_ms: Optional[float]


class SessionStats(BaseModel):
    sample_count: int
    mean_s: Optional[float]
    median_s: Optional[float]
    stdev_s: Optional[float]
    mad_s: Optional[float]


class AnalysisResponse(BaseModel):
    item_stats: List[ItemStats]
    session_stats: SessionStats


@router.get("/analysis", response_model=AnalysisResponse)
def get_analysis(
    station_id: int = Query(..., description="Station ID (required)"),
    test_plan_name: str = Query(..., description="Test plan name / script name (required)"),
    date_from: Optional[date] = Query(None, description="Filter sessions from this date (inclusive)"),
    date_to: Optional[date] = Query(None, description="Filter sessions to this date (inclusive)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Return descriptive statistics for a specific test plan script over a date range.

    - item_stats: per-item execution_duration_ms statistics (mean, median, stdev, MAD)
    - session_stats: total test_duration_seconds statistics across matched sessions
    """
    # --- Build session query ---
    session_q = db.query(TestSessionModel).filter(
        TestSessionModel.station_id == station_id
    )
    if date_from:
        session_q = session_q.filter(TestSessionModel.start_time >= date_from)
    if date_to:
        date_to_end = datetime.combine(date_to, datetime.max.time())
        session_q = session_q.filter(TestSessionModel.start_time <= date_to_end)

    sessions = session_q.all()
    if not sessions:
        return AnalysisResponse(
            item_stats=[],
            session_stats=SessionStats(
                sample_count=0, mean_s=None, median_s=None, stdev_s=None, mad_s=None
            ),
        )

    session_ids = [s.id for s in sessions]

    # --- Session-level stats (total duration) ---
    durations_s = [
        float(s.test_duration_seconds)
        for s in sessions
        if s.test_duration_seconds is not None
    ]
    raw = _compute_stats(durations_s)
    session_stats = SessionStats(
        sample_count=raw["sample_count"],
        mean_s=raw["mean"],
        median_s=raw["median"],
        stdev_s=raw["stdev"],
        mad_s=raw["mad"],
    )

    # --- Get test_plan_ids matching the requested test_plan_name ---
    plan_ids = [
        tp.id
        for tp in db.query(TestPlanModel.id)
        .filter(
            TestPlanModel.station_id == station_id,
            TestPlanModel.test_plan_name == test_plan_name,
        )
        .all()
    ]

    if not plan_ids:
        return AnalysisResponse(item_stats=[], session_stats=session_stats)

    # --- Per-item stats (execution_duration_ms) ---
    results = (
        db.query(TestResultModel)
        .filter(
            TestResultModel.session_id.in_(session_ids),
            TestResultModel.test_plan_id.in_(plan_ids),
        )
        .all()
    )

    # Group by item_no
    item_groups: dict = defaultdict(lambda: {"item_name": "", "durations": []})
    for r in results:
        key = r.item_no
        item_groups[key]["item_name"] = r.item_name
        if r.execution_duration_ms is not None:
            item_groups[key]["durations"].append(float(r.execution_duration_ms))

    item_stats = []
    for item_no in sorted(item_groups.keys()):
        g = item_groups[item_no]
        s = _compute_stats(g["durations"])
        item_stats.append(
            ItemStats(
                item_no=item_no,
                item_name=g["item_name"],
                sample_count=s["sample_count"],
                mean_ms=s["mean"],
                median_ms=s["median"],
                stdev_ms=s["stdev"],
                mad_ms=s["mad"],
            )
        )

    return AnalysisResponse(item_stats=item_stats, session_stats=session_stats)
