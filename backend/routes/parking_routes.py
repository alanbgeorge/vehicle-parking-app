# backend/routes/parking_routes.py

from flask import Blueprint, request, jsonify
from extensions import db, cache_get, cache_set   # ✅ use cache helpers
from models import ParkingLot, ParkingSlot
import json

parking_bp = Blueprint("parking", __name__)


def lot_to_dict_a(_lot_obj):
    """Convert parking lot to dict for user."""
    total_a = ParkingSlot.query.filter_by(lot_id=_lot_obj.id).count()
    busy_a = ParkingSlot.query.filter_by(lot_id=_lot_obj.id, is_occupied=True).count()
    free_a = total_a - busy_a

    return {
        "id": _lot_obj.id,
        "name": _lot_obj.name,
        "address": _lot_obj.address,
        "pin_code": _lot_obj.pin_code,
        "free_slots": free_a,
        "price_per_hour": _lot_obj.price_per_hour,
    }


# -------------------------------------------------
# LIST PARKING LOTS (with Redis cache + pin_code filter)
# -------------------------------------------------
@parking_bp.route("/lots", methods=["GET"])
def list_lots_for_users_a():
    """
    User: list all parking lots.
    Optional query param: pin_code
    Example: /parking/lots?pin_code=560001

    We use Redis to cache results.
    We keep a separate cache key for each pin_code
    (and one for 'all' when no pin_code is provided).
    """
    pin_code_a = request.args.get("pin_code")

    # build a cache key based on pin code
    if pin_code_a:
        cache_key_a = f"parking_lots_user_{pin_code_a}"
    else:
        cache_key_a = "parking_lots_user_all"

    # 1) Try Redis cache first
    try:
        cached_a = cache_get(cache_key_a)
    except RuntimeError:
        # Redis not initialised (safety fallback)
        cached_a = None

    if cached_a:
        print(f"[CACHE] Serving parking lots from Redis cache (key={cache_key_a})")
        data_a = json.loads(cached_a)
        return jsonify(data_a), 200

    print(f"[CACHE] Cache miss for key={cache_key_a}. Querying database...")

    # 2) Not in cache → load from DB
    query_a = ParkingLot.query
    if pin_code_a:
        query_a = query_a.filter_by(pin_code=pin_code_a)

    lots_a = query_a.all()
    result_a = [lot_to_dict_a(lot_a) for lot_a in lots_a]

    # 3) Store in cache for 30 seconds
    try:
        cache_set(cache_key_a, json.dumps(result_a), ex=30)
        print(f"[CACHE] Stored parking lots in Redis (key={cache_key_a}, ttl=30s)")
    except RuntimeError:
        # Redis not initialised, skip caching
        pass

    return jsonify(result_a), 200


# -------------------------------------------------
# LIST SLOTS IN A LOT
# -------------------------------------------------
@parking_bp.route("/lots/<int:lot_id>/slots", methods=["GET"])
def list_slots_in_lot_a(lot_id):
    """
    User: list slots for a given lot.
    Optional query param: only_free=true
    Example: /parking/lots/1/slots?only_free=true
    """
    only_free_a = request.args.get("only_free", "false").lower() == "true"

    lot_a = ParkingLot.query.get(lot_id)
    if not lot_a:
        return jsonify({"message": "Parking lot not found"}), 404

    query_a = ParkingSlot.query.filter_by(lot_id=lot_id)
    if only_free_a:
        query_a = query_a.filter_by(is_occupied=False)

    slots_a = query_a.all()

    slots_result_a = [
        {
            "id": slot_a.id,
            "slot_number": slot_a.slot_number,
            "is_occupied": slot_a.is_occupied,
        }
        for slot_a in slots_a
    ]

    return jsonify(
        {
            "lot": lot_to_dict_a(lot_a),
            "slots": slots_result_a,
        }
    ), 200
