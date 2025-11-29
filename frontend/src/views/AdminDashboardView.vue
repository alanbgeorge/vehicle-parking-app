<template>
  <div class="container mt-4">
    <!-- Header row -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h3 class="mb-1">Admin Dashboard</h3>
        <p class="mb-0 text-muted">
          Manage parking lots, slots and batch jobs.
        </p>
      </div>

      <!-- Batch job buttons -->
      <div class="d-flex flex-column align-items-end">
        <div class="btn-group mb-2">
          <button
            class="btn btn-outline-primary btn-sm"
            :disabled="cleanupLoading"
            @click="runCleanup"
          >
            <span
              v-if="cleanupLoading"
              class="spinner-border spinner-border-sm me-1"
            ></span>
            Run Cleanup Job
          </button>

          <button
            class="btn btn-outline-secondary btn-sm"
            :disabled="dailyLoading"
            @click="runDailyReminders"
          >
            <span
              v-if="dailyLoading"
              class="spinner-border spinner-border-sm me-1"
            ></span>
            Run Daily Reminder Job
          </button>

          <button
            class="btn btn-outline-success btn-sm"
            :disabled="monthlyLoading"
            @click="runMonthlyReport"
          >
            <span
              v-if="monthlyLoading"
              class="spinner-border spinner-border-sm me-1"
            ></span>
            Run Monthly Report Job
          </button>
        </div>

        <small v-if="pageMessage" :class="pageMessageTextClass">
          {{ pageMessage }}
        </small>
      </div>
    </div>

    <!-- Create new lot card -->
    <div class="card mb-3 shadow-sm">
      <div class="card-body">
        <h5 class="card-title mb-3">Create New Parking Lot</h5>

        <form class="row g-3" @submit.prevent="createLot">
          <div class="col-md-4">
            <label class="form-label">Lot Name</label>
            <input
              type="text"
              class="form-control"
              v-model="newLot.name"
              placeholder="e.g. Central Mall Parking"
              required
            />
          </div>

          <div class="col-md-4">
            <label class="form-label">Address</label>
            <input
              type="text"
              class="form-control"
              v-model="newLot.address"
              placeholder="Address"
            />
          </div>

          <div class="col-md-4">
            <label class="form-label">Pin Code</label>
            <input
              type="text"
              class="form-control"
              v-model="newLot.pin_code"
              placeholder="e.g. 560001"
            />
          </div>

          <div class="col-md-3">
            <label class="form-label">Total Slots</label>
            <input
              type="number"
              min="1"
              class="form-control"
              v-model="newLot.total_slots"
              required
            />
          </div>

          <div class="col-md-3">
            <label class="form-label">Price per Hour (₹)</label>
            <input
              type="number"
              min="0"
              step="0.5"
              class="form-control"
              v-model="newLot.price_per_hour"
              required
            />
          </div>

          <div class="col-md-3 d-flex align-items-end">
            <button
              type="submit"
              class="btn btn-success w-100"
              :disabled="createLoading"
            >
              <span
                v-if="createLoading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              Create Lot
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Parking lots table -->
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="card-title mb-3">Existing Parking Lots</h5>

        <p class="text-muted small">
          Shows free and total slots for each parking lot (summary view).
        </p>

        <div v-if="lotsLoading" class="text-muted">
          Loading parking lots...
        </div>

        <table
          v-if="!lotsLoading && lots.length"
          class="table table-bordered table-hover align-middle mb-0"
        >
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Lot Name</th>
              <th>Address</th>
              <th>Pin</th>
              <th>Slots (Free / Total)</th>
              <th>Price / hr (₹)</th>
              <th style="width: 170px;">Actions</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="lot in lots" :key="lot.id">
              <td>{{ lot.id }}</td>
              <td>{{ lot.name }}</td>
              <td>{{ lot.address }}</td>
              <td>{{ lot.pin_code || "-" }}</td>
              <td>
                <span class="badge bg-success me-1">
                  {{ lot.free_slots }} free
                </span>
                /
                <span class="badge bg-secondary ms-1">
                  {{ lot.total_slots }} total
                </span>
              </td>
              <td>₹ {{ lot.price_per_hour }}</td>
              <td>
                <div class="d-flex gap-1">
                  <button
                    class="btn btn-warning btn-sm"
                    @click="startEdit(lot)"
                  >
                    Edit
                  </button>
                  <button
                    class="btn btn-danger btn-sm"
                    :disabled="deleteLoadingId === lot.id"
                    @click="deleteLot(lot.id)"
                  >
                    <span
                      v-if="deleteLoadingId === lot.id"
                      class="spinner-border spinner-border-sm me-1"
                    ></span>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="!lotsLoading && !lots.length" class="text-muted">
          No parking lots created yet.
        </div>
      </div>
    </div>

    <!-- Registered users table -->
    <div class="card shadow-sm mt-3">
      <div class="card-body">
        <h5 class="card-title mb-3">Registered Users</h5>

        <div v-if="usersLoading" class="text-muted">
          Loading users...
        </div>

        <table
          v-if="!usersLoading && users.length"
          class="table table-bordered table-hover align-middle mb-0"
        >
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Joined On</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td>{{ u.name }}</td>
              <td>{{ u.email }}</td>
              <td>{{ u.role }}</td>
              <td>
                <span
                  class="badge"
                  :class="u.is_active ? 'bg-success' : 'bg-secondary'"
                >
                  {{ u.is_active ? "ACTIVE" : "INACTIVE" }}
                </span>
              </td>
              <td>{{ formatDate(u.created_at) }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="!usersLoading && !users.length" class="text-muted">
          No users registered yet.
        </div>
      </div>
    </div>

    <!-- Edit Panel -->
    <div v-if="editLot" class="card mt-3 shadow-sm border-primary">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h5 class="card-title mb-0">
            Edit Parking Lot (ID: {{ editLot.id }})
          </h5>
          <button class="btn-close" @click="cancelEdit"></button>
        </div>

        <form class="row g-3" @submit.prevent="updateLot">
          <div class="col-md-4">
            <label class="form-label">Lot Name</label>
            <input
              type="text"
              class="form-control"
              v-model="editLot.name"
              required
            />
          </div>

          <div class="col-md-4">
            <label class="form-label">Address</label>
            <input
              type="text"
              class="form-control"
              v-model="editLot.address"
            />
          </div>

          <div class="col-md-4">
            <label class="form-label">Pin Code</label>
            <input
              type="text"
              class="form-control"
              v-model="editLot.pin_code"
            />
          </div>

          <div class="col-md-3">
            <label class="form-label">Price per Hour (₹)</label>
            <input
              type="number"
              min="0"
              step="0.5"
              class="form-control"
              v-model="editLot.price_per_hour"
              required
            />
          </div>

          <div class="col-md-3 d-flex align-items-end">
            <button
              type="submit"
              class="btn btn-primary w-100"
              :disabled="updateLoading"
            >
              <span
                v-if="updateLoading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              Save Changes
            </button>
          </div>
        </form>

        <p class="mt-2 mb-0 text-muted small">

        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import axios from "axios";

// list of lots
const lots = ref([]);
const lotsLoading = ref(false);

// new lot form state
const newLot = ref({
  name: "",
  address: "",
  pin_code: "",
  total_slots: "",
  price_per_hour: "",
});

// edit lot state
const editLot = ref(null);

// loading / feedback states
const createLoading = ref(false);
const updateLoading = ref(false);
const deleteLoadingId = ref(null);

// batch job loading states
const cleanupLoading = ref(false);
const dailyLoading = ref(false);
const monthlyLoading = ref(false);

const pageMessage = ref("");
const pageMessageType = ref(""); // "success" or "error"

// users list state
const users = ref([]);
const usersLoading = ref(false);

function setMessage(msg, type = "success") {
  pageMessage.value = msg;
  pageMessageType.value = type;

  setTimeout(() => {
    pageMessage.value = "";
  }, 4000);
}

const pageMessageTextClass = computed(() => {
  if (!pageMessage.value) return "text-muted";
  return pageMessageType.value === "error" ? "text-danger" : "text-success";
});

async function loadLots() {
  lotsLoading.value = true;
  try {
    const res = await axios.get("http://127.0.0.1:5000/admin/parking-lots");
    lots.value = res.data;
  } catch (err) {
    console.error(err);
    setMessage("Failed to load parking lots.", "error");
  } finally {
    lotsLoading.value = false;
  }
}

async function createLot() {
  createLoading.value = true;
  try {
    const payload = {
      name: newLot.value.name,
      address: newLot.value.address,
      pin_code: newLot.value.pin_code,
      total_slots: newLot.value.total_slots,
      price_per_hour: newLot.value.price_per_hour,
    };

    await axios.post("http://127.0.0.1:5000/admin/parking-lots", payload);
    setMessage("Parking lot created successfully.", "success");

    newLot.value = {
      name: "",
      address: "",
      pin_code: "",
      total_slots: "",
      price_per_hour: "",
    };

    await loadLots();
  } catch (err) {
    console.error(err);
    const msg = err.response?.data?.message || "Failed to create parking lot.";
    setMessage(msg, "error");
  } finally {
    createLoading.value = false;
  }
}

function startEdit(lot) {
  editLot.value = { ...lot };
}

function cancelEdit() {
  editLot.value = null;
}

async function updateLot() {
  if (!editLot.value) return;

  updateLoading.value = true;
  try {
    const payload = {
      name: editLot.value.name,
      address: editLot.value.address,
      pin_code: editLot.value.pin_code,
      price_per_hour: editLot.value.price_per_hour,
    };

    await axios.put(
      `http://127.0.0.1:5000/admin/parking-lots/${editLot.value.id}`,
      payload
    );

    setMessage("Parking lot updated successfully.", "success");
    editLot.value = null;
    await loadLots();
  } catch (err) {
    console.error(err);
    const msg =
      err.response?.data?.message || "Failed to update parking lot.";
    setMessage(msg, "error");
  } finally {
    updateLoading.value = false;
  }
}

async function deleteLot(lotId) {
  if (!confirm("Are you sure you want to delete this parking lot?")) return;

  deleteLoadingId.value = lotId;
  try {
    await axios.delete(`http://127.0.0.1:5000/admin/parking-lots/${lotId}`);
    setMessage("Parking lot deleted successfully.", "success");
    await loadLots();
  } catch (err) {
    console.error(err);
    const msg =
      err.response?.data?.message ||
      "Failed to delete parking lot. Make sure all slots are free.";
    setMessage(msg, "error");
  } finally {
    deleteLoadingId.value = null;
  }
}

// --------- users loading ---------

async function loadUsers() {
  usersLoading.value = true;
  try {
    const res = await axios.get("http://127.0.0.1:5000/admin/users");
    users.value = res.data;
  } catch (err) {
    console.error(err);
    setMessage("Failed to load users.", "error");
  } finally {
    usersLoading.value = false;
  }
}

function formatDate(value) {
  if (!value) return "-";
  try {
    const d = new Date(value);
    return d.toLocaleDateString();
  } catch (e) {
    return value;
  }
}

// --------- batch job actions -------------

async function runCleanup() {
  cleanupLoading.value = true;
  try {
    const res = await axios.post(
      "http://127.0.0.1:5000/admin/run-cleanup"
    );
    setMessage(
      `Cleanup job started (task ID: ${res.data.task_id || "N/A"})`,
      "success"
    );
  } catch (err) {
    console.error(err);
    setMessage("Failed to start cleanup job.", "error");
  } finally {
    cleanupLoading.value = false;
  }
}

async function runDailyReminders() {
  dailyLoading.value = true;
  try {
    const res = await axios.post(
      "http://127.0.0.1:5000/admin/run-daily-reminders"
    );
    setMessage(
      `Daily reminder job started (task ID: ${res.data.task_id || "N/A"})`,
      "success"
    );
  } catch (err) {
    console.error(err);
    setMessage("Failed to start daily reminder job.", "error");
  } finally {
    dailyLoading.value = false;
  }
}

async function runMonthlyReport() {
  monthlyLoading.value = true;
  try {
    const res = await axios.post(
      "http://127.0.0.1:5000/admin/run-monthly-report"
    );
    setMessage(
      `Monthly report job started (task ID: ${res.data.task_id || "N/A"})`,
      "success"
    );
  } catch (err) {
    console.error(err);
    setMessage("Failed to start monthly report job.", "error");
  } finally {
    monthlyLoading.value = false;
  }
}

onMounted(() => {
  loadLots();
  loadUsers();
});
</script>

<style scoped>
.card {
  border-radius: 10px;
}
</style>
