<script setup>
import { ref, onMounted, computed } from "vue";
import axios from "axios";
import { useRoute, useRouter } from "vue-router";
import { currentUser } from "../userStore";

const route = useRoute();
const router = useRouter();
const lotId = route.params.id;

// reactive data
const lotDetails = ref(null);
const slots = ref([]);
const vehicleNumber = ref("");

const loading = ref(false);
const bookingLoading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const currentUserLocal = computed(() => currentUser.value || null);

// Load slots + lot details from backend
async function loadData() {
  errorMessage.value = "";
  successMessage.value = "";
  loading.value = true;

  try {
    const res = await axios.get(
      `http://127.0.0.1:5000/parking/lots/${lotId}/slots`
    );

    lotDetails.value = res.data.lot;
    slots.value = res.data.slots;
  } catch (err) {
    console.error(err);
    errorMessage.value =
      "Failed to load slots for this parking lot. Please try again.";
  } finally {
    loading.value = false;
  }
}

async function bookSlot(slotId) {
  errorMessage.value = "";
  successMessage.value = "";

  if (!currentUserLocal.value || !currentUserLocal.value.id) {
    errorMessage.value = "You must be logged in to book a slot.";
    return;
  }

  if (!vehicleNumber.value || vehicleNumber.value.trim() === "") {
    errorMessage.value = "Please enter your vehicle number.";
    return;
  }

  bookingLoading.value = true;

  try {
    const res = await axios.post("http://127.0.0.1:5000/parking/book", {
      user_id: currentUserLocal.value.id,
      slot_id: slotId,
      vehicle_number: vehicleNumber.value.trim(),
    });

    successMessage.value = "Slot booked successfully!";
    console.log("Booking ID:", res.data.booking_id);

    // refresh slots to update occupied/free status
    await loadData();
  } catch (err) {
    console.error(err);
    if (err.response && err.response.data && err.response.data.message) {
      errorMessage.value = err.response.data.message;
    } else {
      errorMessage.value = "Failed to book the slot. Please try again.";
    }
  } finally {
    bookingLoading.value = false;
  }
}

function goBack() {
  router.push("/user-dashboard");
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="container mt-4">
    <!-- Top bar -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3 class="mb-0">Parking Slots</h3>
      <button class="btn btn-outline-secondary btn-sm" @click="goBack">
        ← Back to Dashboard
      </button>
    </div>

    <!-- Lot details card -->
    <div v-if="lotDetails" class="card mb-3 shadow-sm">
      <div class="card-body">
        <h5 class="card-title mb-1">{{ lotDetails.name }}</h5>
        <p class="mb-1 text-muted">
          {{ lotDetails.address }}<br />
          Pin: <strong>{{ lotDetails.pin_code || "N/A" }}</strong>
        </p>

        <p class="mb-1">
          <span class="badge bg-success me-2">
            Free Slots: {{ lotDetails.free_slots }}
          </span>
        </p>

        <p class="mb-0">
          <small>
            Price per hour:
            <strong>₹ {{ lotDetails.price_per_hour }}</strong>
          </small>
        </p>
      </div>
    </div>

    <!-- Messages -->
    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
    </div>

    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <!-- Vehicle number input -->
    <div class="card mb-3 shadow-sm">
      <div class="card-body">
        <h6 class="card-title mb-2">Enter Vehicle Number</h6>
        <div class="row g-2 align-items-center">
          <div class="col-md-6">
            <input
              type="text"
              class="form-control"
              v-model="vehicleNumber"
              placeholder="e.g. TN 01 AB 1234"
            />
          </div>
          <div class="col-md-6">
            <small class="text-muted">
              Select a free slot below and click <strong>Book</strong>.
            </small>
          </div>
        </div>
      </div>
    </div>

    <!-- Slots table -->
    <div class="card shadow-sm">
      <div class="card-body">
        <h6 class="card-title mb-3">Slots in this Parking Lot</h6>

        <div v-if="loading" class="text-muted">
          Loading slots...
        </div>

        <table
          v-if="!loading && slots.length"
          class="table table-bordered table-hover align-middle mb-0"
        >
          <thead class="table-light">
            <tr>
              <th style="width: 15%">Slot ID</th>
              <th style="width: 25%">Slot Number</th>
              <th style="width: 20%">Status</th>
              <th style="width: 40%">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="slot in slots" :key="slot.id">
              <td>{{ slot.id }}</td>
              <td>{{ slot.slot_number }}</td>
              <td>
                <span
                  class="badge"
                  :class="slot.is_occupied ? 'bg-danger' : 'bg-success'"
                >
                  {{ slot.is_occupied ? "Occupied" : "Available" }}
                </span>
              </td>
              <td>
                <button
                  class="btn btn-sm"
                  :class="slot.is_occupied ? 'btn-secondary' : 'btn-primary'"
                  :disabled="slot.is_occupied || bookingLoading"
                  @click="bookSlot(slot.id)"
                >
                  <span v-if="!slot.is_occupied && bookingLoading" class="spinner-border spinner-border-sm me-1"></span>
                  <span v-if="slot.is_occupied">Not Available</span>
                  <span v-else>Book this Slot</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="!loading && !slots.length" class="text-muted">
          No slots found for this parking lot.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  border-radius: 10px;
}
</style>
