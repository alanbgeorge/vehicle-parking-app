<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-4">
        <div class="card shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-center mb-3">Vehicle Parking System</h3>
            <h5 class="text-center mb-4">Login</h5>

            <!-- Error Alert -->
            <div v-if="errorMessage" class="alert alert-danger py-2">
              {{ errorMessage }}
            </div>

            <!-- Form -->
            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label class="form-label">Email</label>
                <input
                  type="email"
                  class="form-control"
                  v-model="email"
                  placeholder="Enter your email"
                  required
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Password</label>
                <input
                  type="password"
                  class="form-control"
                  v-model="password"
                  placeholder="Enter your password"
                  required
                />
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="loading"
              >
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span v-if="loading">Logging in...</span>
                <span v-else>Login</span>
              </button>
            </form>

            <!-- Register Link -->
            <div class="text-center mt-3">
              <small>
                Don't have an account?
                <a href="#" @click.prevent="goToRegister">Register here</a>
              </small>
            </div>

            <!-- Info for Admin -->

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";
import { saveUserToStorage } from "../userStore";

const router = useRouter();

const email = ref("");
const password = ref("");
const loading = ref(false);
const errorMessage = ref("");

async function handleLogin() {
  errorMessage.value = "";
  loading.value = true;

  try {
    const res = await axios.post("http://127.0.0.1:5000/auth/login", {
      email: email.value,
      password: password.value,
    });

    const user = res.data.user;
    // Save to localStorage + store
    saveUserToStorage(user);

    // Redirect based on role
    if (user.role === "ADMIN") {
      router.push("/admin-dashboard");
    } else {
      router.push("/user-dashboard");
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      errorMessage.value = err.response.data.message;
    } else {
      errorMessage.value = "Something went wrong. Please try again.";
    }
  } finally {
    loading.value = false;
  }
}

function goToRegister() {
  router.push("/register");
}
</script>

<style scoped>
.card {
  border-radius: 10px;
}
</style>
