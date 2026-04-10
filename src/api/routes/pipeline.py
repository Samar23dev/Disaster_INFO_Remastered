"""POST /api/pipeline/run - Manually trigger pipeline"""

from fastapi import APIRouter, BackgroundTasks
from datetime import datetime

router = APIRouter(tags=["Pipeline"])


@router.post("/pipeline/run")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Manually trigger the classification pipeline.
    Runs in background to avoid blocking the API response.
    """
    from src.classifiers.pipeline import run_pipeline
    
    # Run pipeline in background
    background_tasks.add_task(run_pipeline)
    
    return {
        "status": "triggered",
        "message": "Pipeline execution started in background",
        "timestamp": datetime.now().isoformat()
    }
