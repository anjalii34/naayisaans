from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tables import User, RecoveryTask, TaskCompletion, TwinState, RecoveryEvent
from app.schemas import TaskOut, TaskCompleteRequest
from app.auth import get_current_user

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = db.query(RecoveryTask).all()

    # Light personalization: when risk/stress is elevated, surface breathing/
    # distraction-style tasks first. Falls back to catalog order otherwise.
    twin = db.query(TwinState).filter(TwinState.user_id == current_user.id).first()
    if twin and twin.risk_level in ("moderate", "high"):
        priority = {"breathing": 0, "wellness": 1, "general": 2, "social": 3}
        tasks = sorted(tasks, key=lambda t: priority.get(t.category, 4))

    return tasks


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    payload: TaskCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(RecoveryTask).filter(RecoveryTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    completion = TaskCompletion(
        user_id=current_user.id,
        task_id=task_id,
        craving_before=payload.craving_before,
        craving_after=payload.craving_after,
    )
    db.add(completion)

    db.add(RecoveryEvent(
        user_id=current_user.id,
        event_type="task",
        title=f"Completed: {task.title}",
        description=(
            f"Craving went from {payload.craving_before} to {payload.craving_after}"
            if payload.craving_before is not None and payload.craving_after is not None
            else "Task completed"
        ),
    ))
    db.commit()

    delta = None
    if payload.craving_before is not None and payload.craving_after is not None:
        delta = payload.craving_before - payload.craving_after

    return {"status": "saved", "task": task.title, "craving_delta": delta}


@router.get("/tasks/history")
def task_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(TaskCompletion, RecoveryTask)
        .join(RecoveryTask, TaskCompletion.task_id == RecoveryTask.id)
        .filter(TaskCompletion.user_id == current_user.id)
        .order_by(TaskCompletion.timestamp.desc())
        .limit(30)
        .all()
    )
    return {
        "history": [
            {
                "task": task.title,
                "craving_before": completion.craving_before,
                "craving_after": completion.craving_after,
                "timestamp": completion.timestamp,
            }
            for completion, task in rows
        ]
    }
