<template>
  <div class="container mt-4">
    <!-- Header row -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h3 class="mb-1">User Dashboard</h3>
        <p class="mb-0 text-muted">
          Welcome,
          <strong>{{ currentUserLocal?.name || "Guest" }}</strong>
          <span v-if="currentUserLocal && currentUserLocal.email">
            ({{ currentUserLocal.email }})
          </span>
        </p>
      </div>

      <div class="d-flex gap-2">
        <button class="btn btn-outline-secondary btn-sm" @click="goToHistory">
          View Booking History
        </button>
      </div>
    </div>

    <!-- Search / Filter row -->
    <div class="card mb-3 shadow-sm">
      <div class="card-body">
        <form class="row g-2 align-items-end" @submit.prevent="loadLots">
          <div class="col-md-4">
            <label class="form-label mb-1">Filter by Pin Code (optional)</label>
            <input
              type="text"
              class="form-control"
              v-model="pinCode"
              placeholder="Enter pin code (e.g. 560001)"
            />
          </div>

          <div class="col-md-3">
            <button
              type="submit"
              class="btn btn-primary w-100"
              :disabled="loading"
            >
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              <span v-if="loading">Loading...</span>
              <span v-else>Search Lots</span>
            </button>
          </div>

          <div class="col-md-3">
            <button
              type="button"
              class="btn btn-outline-secondary w-100"
              @click="resetFilter"
              :disabled="loading"
            >
              Clear Filter
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
    </div>

    <!-- Lots list -->
    <div v-if="lots.length === 0 && !loading" class="text-muted">
      No parking lots found. Please try another pin code or contact admin.
    </div>

    <div class="row g-3">
      <div
        v-for="lot in lots"
        :key="lot.id"
        class="col-md-4"
      >
        <div class="card h-100 shadow-sm">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title mb-1">{{ lot.name }}</h5>
            <p class="card-text mb-1">
              <small class="text-muted">
                {{ lot.address }}<br />
                Pin: <strong>{{ lot.pin_code || "N/A" }}</strong>
              </small>
            </p>

            <p class="mb-1">
              <span class="badge bg-success me-2">
                Free Slots: {{ lot.free_slots }}
              </span>
            </p>

            <p class="mb-2">
              <small>
                Price per hour:
                <strong>₹ {{ lot.price_per_hour }}</strong>
              </small>
            </p>

            <div class="mt-auto">
              <button
                class="btn btn-primary w-100"
                @click="goToSlots(lot.id)"
              >
                View Slots & Book
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-if="loading" class="mt-3 text-center text-muted">
      Loading parking lots...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";
import { currentUser } from "../userStore";

const router = useRouter();

const lots = ref([]);
const pinCode = ref("");
const loading = ref(false);
const errorMessage = ref("");

const currentUserLocal = computed(() => currentUser.value || null);

async function loadLots() {
  errorMessage.value = "";
  loading.value = true;

  try {
    let url = "http://127.0.0.1:5000/parking/lots";

    if (pinCode.value && pinCode.value.trim() !== "") {
      const encoded = encodeURIComponent(pinCode.value.trim());
      url += `?pin_code=${encoded}`;
    }

    const res = await axios.get(url);
    lots.value = res.data;
  } catch (err) {
    console.error(err);
    errorMessage.value = "Failed to load parking lots. Please try again.";
  } finally {
    loading.value = false;
  }
}

function resetFilter() {
  pinCode.value = "";
  loadLots();
}

function goToSlots(lotId) {
  router.push(`/slots/${lotId}`);
}

function goToHistory() {
  router.push("/history");
}

// Load lots when the page opens
onMounted(() => {
  loadLots();
});
</script>

<style scoped>
.card {
  border-radius: 10px;
}
</style>
