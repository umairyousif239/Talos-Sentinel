import io
import csv
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.api.login import get_current_user

from backend.modules.alert_loop import latest_alert
from backend.modules.alert_store import (
    get_connection,
    fetch_alert_history,
    fetch_latest_alert
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/latest", dependencies=[Depends(get_current_user)])
def get_latest():
    """
    Returns most recent alert (if any)
    """
    alert = fetch_latest_alert()
    return alert or {"status": "NO_ALERT"}

@router.get("/history", dependencies=[Depends(get_current_user)])
def get_history(limit: int = 100):
    """
    returns the last 100 triggered alerts
    """
    return fetch_alert_history(limit)

@router.get("/export")
def export_alerts(username:str = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    
    # Creates the CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    if rows:
        # Writes the column headers dynamically
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(row)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=incident_report.csv"}
    )