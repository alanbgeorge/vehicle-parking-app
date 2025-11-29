# backend/routes/export_routes.py

from flask import Blueprint, request, jsonify, send_file
from extensions import db
from models import ExportJob

export_bp = Blueprint("export", __name__, url_prefix="/api/exports")


# -------------------------------------------------
# START CSV EXPORT JOB
# -------------------------------------------------
@export_bp.route("/bookings", methods=["POST"])
def start_export_bookings():
    # 👉 Import here to avoid circular import
    from celery_worker import export_user_bookings_csv

    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"message": "user_id is required"}), 400

    # Create ExportJob row
    job = ExportJob(user_id=user_id, status="PENDING")
    db.session.add(job)
    db.session.commit()

    # Trigger Celery async task
    export_user_bookings_csv.delay(job.id)

    return jsonify({
        "message": "Export started",
        "export_id": job.id,
        "status": job.status,
    }), 202


# -------------------------------------------------
# CHECK STATUS + DOWNLOAD FILE
# -------------------------------------------------
@export_bp.route("/bookings/<int:export_id>", methods=["GET"])
def export_status(export_id):
    job = ExportJob.query.get_or_404(export_id)

    if job.status != "DONE":
        return jsonify({
            "export_id": job.id,
            "status": job.status,
            "error_message": job.error_message,
        }), 200

    if not job.file_path:
        return jsonify({
            "export_id": job.id,
            "status": "FAILED",
            "error_message": "File not found",
        }), 500

    return send_file(
        job.file_path,
        as_attachment=True,
        mimetype="text/csv"
    )
