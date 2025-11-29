# backend/routes/booking_routes.py

from flask import Blueprint, request, jsonify
from datetime import datetime
import math   # for hour rounding

from extensions import db
from models import ParkingSlot, Booking, ParkingLot

booking_bp = Blueprint("booking", __name__)


# -------------------------------------------------
# BOOK SLOT
# -------------------------------------------------
@booking_bp.route("/book", methods=["POST"])
def book_slot():
    data = request.get_json() or {}

    user_id = data.get("user_id")
    slot_id = data.get("slot_id")
    vehicle_number = data.get("vehicle_number")

    if not user_id or not slot_id or not vehicle_number:
        return jsonify({"message": "user_id, slot_id and vehicle_number are required"}), 400

    slot = ParkingSlot.query.get(slot_id)
    if not slot:
        return jsonify({"message": "Slot not found"}), 404

    if slot.is_occupied:
        return jsonify({"message": "Slot already booked"}), 400

    # Mark slot occupied
    slot.is_occupied = True

    # Create booking
    booking = Booking(
        user_id=user_id,
        slot_id=slot_id,
        vehicle_number=vehicle_number,
        start_time=datetime.utcnow(),
        status="ACTIVE",
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({
        "message": "Slot booked successfully",
        "booking_id": booking.id,
    }), 201


# -------------------------------------------------
# RELEASE SLOT (WITH AMOUNT CALCULATION)
# -------------------------------------------------
@booking_bp.route("/release", methods=["POST"])
def release_slot():
    data = request.get_json() or {}

    # Accept booking_id or id
    booking_id = data.get("booking_id") or data.get("id")

    if not booking_id:
        return jsonify({"message": "booking_id is required"}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"message": "Booking not found"}), 404

    if booking.status != "ACTIVE":
        return jsonify({"message": "Booking already completed"}), 400

    slot = ParkingSlot.query.get(booking.slot_id)
    if not slot:
        return jsonify({"message": "Linked parking slot not found"}), 400

    # Free slot
    slot.is_occupied = False

    # Complete booking
    now = datetime.utcnow()
    booking.end_time = now
    booking.status = "COMPLETED"

    # -----------------------------------------------
    # AMOUNT CALCULATION LOGIC
    # -----------------------------------------------
    amount = 0.0

    if booking.start_time:
        # Duration in hours
        total_seconds = (now - booking.start_time).total_seconds()
        hours = total_seconds / 3600

        # Bill full hours (rounded up)
        billed_hours = max(1, math.ceil(hours))

        # Get lot price
        lot = ParkingLot.query.get(slot.lot_id)
        if lot and hasattr(lot, "price_per_hour"):
            amount = billed_hours * lot.price_per_hour

    booking.amount = amount

    db.session.commit()

    return jsonify({
        "message": "Slot released successfully",
        "amount": booking.amount,
        "hours_charged": billed_hours,
    }), 200


# -------------------------------------------------
# BOOKING HISTORY FOR A USER (WITH AMOUNT)
# -------------------------------------------------
@booking_bp.route("/history/<int:user_id>", methods=["GET"])
def booking_history(user_id):
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.id.desc()).all()

    result = []
    for b in bookings:
        result.append({
            "booking_id": b.id,
            "slot_id": b.slot_id,
            "vehicle_number": b.vehicle_number,
            "start_time": b.start_time.isoformat() if b.start_time else None,
            "end_time": b.end_time.isoformat() if b.end_time else None,
            "status": b.status,
            "amount": b.amount,  # NEW
        })

    return jsonify(result), 200
