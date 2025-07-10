# utils/helpers.py

def format_task(task):
    """
    Returns a dict representation of a task.
    """
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "category": task.category,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None
    }

# You can add more utilities here, e.g., for exporting reports
