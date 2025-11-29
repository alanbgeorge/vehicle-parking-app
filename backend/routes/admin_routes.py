# backend/routes/admin_routes.py

from flask import Blueprint, request, jsonify
from extensions import db, get_redis
from models import ParkingLot, ParkingSlot, Booking, User

admin_bp = Blueprint("admin", __name__)


def lot_to_dict_a(_lot_obj):
    """Helper: convert ParkingLot to dict with slot info."""
    total_a = ParkingSlot.query.filter_by(lot_id=_lot_obj.id).count()
    busy_a = ParkingSlot.query.filter_by(
        lot_id=_lot_obj.id, is_occupied=True
    ).count()
    free_a = total_a - busy_a

    return {
        "id": _lot_obj.id,
        "name": _lot_obj.name,
        "address": _lot_obj.address,
        "pin_code": _lot_obj.pin_code,
        "total_slots": total_a,
        "free_slots": free_a,
        "price_per_hour": _lot_obj.price_per_hour,
    }


# ------------------------------------------
# CREATE NEW PARKING LOT
# ------------------------------------------
@admin_bp.route("/parking-lots", methods=["POST"])
def create_parking_lot_a():
    data_a = request.get_json() or {}

    name_a = data_a.get("name")
    address_a = data_a.get("address")
    pin_code_a = data_a.get("pin_code")
    total_slots_a = data_a.get("total_slots")
    price_a = data_a.get("price_per_hour")

    if not name_a or not total_slots_a or price_a is None:
        return (
            jsonify(
                {
                    "message": (
                        "Please provide name, total_slots and price_per_hour"
                    )
                }
            ),
            400,
        )

    try:
        total_slots_a = int(total_slots_a)
    except Exception:
        return jsonify({"message": "total_slots must be an integer"}), 400

    try:
        price_a = float(price_a)
    except Exception:
        return jsonify({"message": "price_per_hour must be a number"}), 400

    lot_a = ParkingLot(
        name=name_a,
        address=address_a,
        pin_code=pin_code_a,
        total_slots=total_slots_a,
        price_per_hour=price_a,
    )
    db.session.add(lot_a)
    db.session.commit()

    # create slots S1 ... S{total}
    for num_a in range(1, total_slots_a + 1):
        slot_a = ParkingSlot(
            lot_id=lot_a.id,
            slot_number=f"S{num_a}",
            is_occupied=False,
        )
        db.session.add(slot_a)

    db.session.commit()

    # ✅ CLEAR CACHE after creating parking lot
    try:
        redis = get_redis()
        redis.delete("parking_lots_user_all")
        if pin_code_a:
            redis.delete(f"parking_lots_user_{pin_code_a}")
        print("[CACHE] Invalidated parking lot cache after CREATE")
    except Exception:
        pass

    return (
        jsonify(
            {
                "message": "Parking lot created successfully",
                "lot": lot_to_dict_a(lot_a),
            }
        ),
        201,
    )


# ------------------------------------------
# LIST ALL PARKING LOTS
# ------------------------------------------
@admin_bp.route("/parking-lots", methods=["GET"])
def get_all_lots_a():
    lots_a = ParkingLot.query.all()
    output_a = [lot_to_dict_a(l) for l in lots_a]
    return jsonify(output_a), 200


# ------------------------------------------
# UPDATE A PARKING LOT
# ------------------------------------------
@admin_bp.route("/parking-lots/<int:lot_id>", methods=["PUT"])
def update_lot_a(lot_id):
    data_a = request.get_json() or {}

    lot_a = ParkingLot.query.get(lot_id)
    if not lot_a:
        return jsonify({"message": "Parking lot not found"}), 404

    lot_a.name = data_a.get("name", lot_a.name)
    lot_a.address = data_a.get("address", lot_a.address)
    lot_a.pin_code = data_a.get("pin_code", lot_a.pin_code)

    price_val_a = data_a.get("price_per_hour", lot_a.price_per_hour)
    try:
        lot_a.price_per_hour = float(price_val_a)
    except Exception:
        return jsonify({"message": "price_per_hour must be a number"}), 400

    db.session.commit()

    #  CLEAR CACHE after updating parking lot
    try:
        redis = get_redis()
        redis.delete("parking_lots_user_all")
        if lot_a.pin_code:
            redis.delete(f"parking_lots_user_{lot_a.pin_code}")
        print("[CACHE] Invalidated parking lot cache after UPDATE")
    except Exception:
        pass

    return (
        jsonify(
            {
                "message": "Parking lot updated",
                "lot": lot_to_dict_a(lot_a),
            }
        ),
        200,
    )


# ------------------------------------------
# DELETE A PARKING LOT
# ------------------------------------------
@admin_bp.route("/parking-lots/<int:lot_id>", methods=["DELETE"])
def delete_lot_a(lot_id):
    lot_a = ParkingLot.query.get(lot_id)
    if not lot_a:
        return jsonify({"message": "Parking lot not found"}), 404

    # Spec: Delete only if all slots in this lot are free
    busy_count = ParkingSlot.query.filter_by(
        lot_id=lot_id, is_occupied=True
    ).count()
    if busy_count > 0:
        return (
            jsonify(
                {
                    "message": (
                        "Failed to delete parking lot. Make sure all slots are free."
                    )
                }
            ),
            400,
        )

    # collect slot ids first
    slots_a = ParkingSlot.query.filter_by(lot_id=lot_id).all()
    slot_ids_a = [s.id for s in slots_a]

    # delete bookings linked to these slots
    if slot_ids_a:
        Booking.query.filter(Booking.slot_id.in_(slot_ids_a)).delete(
            synchronize_session=False
        )

    # delete slots
    ParkingSlot.query.filter_by(lot_id=lot_id).delete()

    pin_code_to_clear = lot_a.pin_code

    db.session.delete(lot_a)
    db.session.commit()

    #  CLEAR CACHE after deleting parking lot
    try:
        redis = get_redis()
        redis.delete("parking_lots_user_all")
        if pin_code_to_clear:
            redis.delete(f"parking_lots_user_{pin_code_to_clear}")
        print("[CACHE] Invalidated parking lot cache after DELETE")
    except Exception:
        pass

    return jsonify({"message": "Parking lot deleted"}), 200


# ------------------------------------------
# LIST USERS (non-admin) + ACTIVE / INACTIVE
# ------------------------------------------
@admin_bp.route("/users", methods=["GET"])
def list_users_a():
    """
    Return all NON-ADMIN users for the Admin dashboard.

    is_active = True  if user has at least one ACTIVE booking
                 False otherwise
    """
    users_a = (
        User.query.filter(User.role != "ADMIN")
        .order_by(User.id.asc())
        .all()
    )

    result_a = []
    for u in users_a:
        has_active = (
            Booking.query.filter_by(user_id=u.id, status="ACTIVE").count() > 0
        )

        result_a.append(
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "is_active": has_active,  # ✅ for UI badge
            }
        )

    return jsonify(result_a), 200


# ------------------------------------------
# RUN CELERY CLEANUP TASK
# ------------------------------------------
@admin_bp.route("/run-cleanup", methods=["POST"])
def run_cleanup_a():
    from celery_worker import cleanup_stale_bookings_a

    task_a = cleanup_stale_bookings_a.delay()

    return jsonify(
        {
            "message": "Cleanup started",
            "task_id": task_a.id,
        }
    ), 202


# ------------------------------------------
# RUN DAILY REMINDERS TASK
# ------------------------------------------
@admin_bp.route("/run-daily-reminders", methods=["POST"])
def run_daily_reminders_a():
    from celery_worker import send_daily_reminders_a

    task = send_daily_reminders_a.delay()

    return jsonify(
        {
            "message": "Daily reminder job started",
            "task_id": task.id,
        }
    ), 202


# ------------------------------------------
# RUN MONTHLY REPORT TASK
# ------------------------------------------
@admin_bp.route("/run-monthly-report", methods=["POST"])
def run_monthly_report_a():
    from celery_worker import send_monthly_activity_report_a

    task = send_monthly_activity_report_a.delay()

    return jsonify(
        {
            "message": "Monthly report job started",
            "task_id": task.id,
        }
    ), 202
