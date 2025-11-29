<template>
  <div class="container mt-4">
    <!-- Header row -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h3 class="mb-1">Booking History</h3>

      </div>

      <button class="btn btn-outline-secondary btn-sm" @click="goDashboard">
        ← Back to Dashboard
      </button>
    </div>

    <!-- Message if not logged in or error -->
    <div v-if="message" class="alert alert-info">
      {{ message }}
    </div>

    <!-- Export section -->
    <div v-if="userId" class="card mb-3 shadow-sm">
      <div class="card-body">
        


        <button
          class="btn btn-warning me-2"
          :disabled="exportLoading || !bookings.length"
          @click="startExport"
        >
          <span
            v-if="exportLoading"
            class="spinner-border spinner-border-sm me-1"
          ></span>
          Export Bookings as CSV
        </button>

        <button
          v-if="exportId"
          class="btn btn-success"
          @click="downloadExport"
        >
          Download CSV
        </button>

        <p v-if="exportMsg" class="small text-muted mt-2 mb-0">
          {{ exportMsg }}
        </p>
      </div>
    </div>

    <!-- Booking history table -->
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="card-title mb-3">Your Bookings</h5>

        <div v-if="loading" class="text-muted">
          Loading booking history...
        </div>

        <table
          v-if="!loading && bookings.length"
          class="table table-bordered table-hover align-middle mb-0"
        >
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Slot ID</th>
              <th>Vehicle No.</th>
              <th>Start Time</th>
              <th>End Time</th>
              <th>Amount (₹)</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <!-- use booking_id from backend -->
            <tr v-for="b in bookings" :key="b.booking_id">
              <td>{{ b.booking_id }}</td>
              <td>{{ b.slot_id }}</td>
              <td>{{ b.vehicle_number || "-" }}</td>
              <td>{{ formatDateTime(b.start_time) }}</td>
              <td>{{ formatDateTime(b.end_time) }}</td>

              <!-- formatted amount -->
              <td>
                <span v-if="b.status === 'COMPLETED' && b.amount != null">
                  {{ formatAmount(b.amount) }}
                </span>
                <span v-else>-</span>
              </td>

              <td>
                <span
                  class="badge"
                  :class="b.status === 'ACTIVE' ? 'bg-success' : 'bg-secondary'"
                >
                  {{ b.status }}
                </span>
              </td>

              <!-- RELEASE BUTTON for ACTIVE bookings -->
              <td>
                <button
                  v-if="b.status === 'ACTIVE'"
                  class="btn btn-sm btn-danger"
                  @click="releaseBooking(b.booking_id)"
                >
                  Release Slot
                </button>
                <span v-else class="text-muted small">-</span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="!loading && !bookings.length" class="text-muted">
          No bookings found yet.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";

const router = useRouter();

// state
const bookings = ref([]);
const loading = ref(false);
const message = ref("");

const userId = ref(null);

// export job state
const exportId = ref(null);
const exportMsg = ref("");
const exportLoading = ref(false);

// go back to user dashboard
function goDashboard() {
  router.push("/user-dashboard");
}

// load logged-in user from localStorage
function loadUserFromStorage() {
  const raw = localStorage.getItem("vps_user");
  if (!raw) {
    message.value = "Please login to see your booking history.";
    return;
  }

  try {
    const user = JSON.parse(raw);
    userId.value = user.id;
  } catch (e) {
    console.error("Bad vps_user in storage", e);
    localStorage.removeItem("vps_user");
    message.value = "Please login again.";
  }
}

// load booking history for this user
async function loadHistory() {
  if (!userId.value) {
    return;
  }

  loading.value = true;
  message.value = "";

  try {
    const res = await axios.get(
      `http://127.0.0.1:5000/parking/history/${userId.value}`
    );
    bookings.value = res.data;
  } catch (err) {
    console.error(err);
    message.value =
      err.response?.data?.message || "Failed to load booking history.";
  } finally {
    loading.value = false;
  }
}

// start async CSV export (calls Celery job)
async function startExport() {
  if (!userId.value) {
    exportMsg.value = "Please login before exporting.";
    return;
  }

  exportLoading.value = true;
  exportMsg.value = "Starting export...";
  exportId.value = null;

  try {
    const res = await axios.post(
      "http://127.0.0.1:5000/api/exports/bookings",
      {
        user_id: userId.value,
      }
    );

    exportId.value = res.data.export_id;
    exportMsg.value =
      res.data.message || "Export started. Click 'Download CSV' when ready.";
  } catch (err) {
    console.error(err);
    exportMsg.value =
      err.response?.data?.message || "Failed to start export.";
  } finally {
    exportLoading.value = false;
  }
}

// open download link in new tab
function downloadExport() {
  if (!exportId.value) return;

  const url = `http://127.0.0.1:5000/api/exports/bookings/${exportId.value}`;
  window.open(url, "_blank");
}

// call backend to release a booking
async function releaseBooking(bookingId) {
  if (!bookingId) return;

  const ok = window.confirm("Are you sure you want to release this slot?");
  if (!ok) return;

  try {
    const res = await axios.post("http://127.0.0.1:5000/parking/release", {
      booking_id: bookingId,
    });

    const amt = res.data.amount;
    if (amt != null) {
      alert(
        `Slot released successfully.\nAmount charged: ₹${Number(amt).toFixed(
          2
        )}`
      );
    } else {
      alert("Slot released successfully.");
    }

    // reload history so status/amount updates
    await loadHistory();
  } catch (err) {
    console.error(err);
    alert(
      err.response?.data?.message ||
        "Failed to release slot. Please try again."
    );
  }
}

// simple formatter for datetime strings
function formatDateTime(value) {
  if (!value) return "-";
  try {
    const d = new Date(value);
    return d.toLocaleString();
  } catch (e) {
    return value;
  }
}

// simple formatter for amount
function formatAmount(value) {
  if (value == null) return "-";
  const num = Number(value);
  if (isNaN(num)) return value;
  return num.toFixed(2);
}

onMounted(async () => {
  loadUserFromStorage();
  if (userId.value) {
    await loadHistory();
  }
});
</script>

<style scoped>
.card {
  border-radius: 10px;
}
</style>
