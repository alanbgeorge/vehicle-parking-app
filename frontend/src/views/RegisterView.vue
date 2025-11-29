<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-4">
        <div class="card shadow-sm">
          <div class="card-body">
            <h3 class="card-title text-center mb-3">Vehicle Parking System</h3>
            <h5 class="text-center mb-4">Register</h5>

            <!-- Error Alert -->
            <div v-if="errorMessage" class="alert alert-danger py-2">
              {{ errorMessage }}
            </div>

            <!-- Success Alert -->
            <div v-if="successMessage" class="alert alert-success py-2">
              {{ successMessage }}
            </div>

            <form @submit.prevent="handleRegister">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input
                  type="text"
                  class="form-control"
                  v-model="name"
                  placeholder="Enter your name"
                  required
                />
              </div>

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
                  placeholder="Enter a password"
                  required
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Confirm Password</label>
                <input
                  type="password"
                  class="form-control"
                  v-model="confirmPassword"
                  placeholder="Re-enter your password"
                  required
                />
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="loading"
              >
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span v-if="loading">Registering...</span>
                <span v-else>Register</span>
              </button>
            </form>

            <div class="text-center mt-3">
              <small>
                Already have an account?
                <a href="#" @click.prevent="goToLogin">Login here</a>
              </small>
            </div>

            <div class="mt-3">
              <small class="text-muted">
              </small>
            </div>
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

const name = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");

const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

async function handleRegister() {
  errorMessage.value = "";
  successMessage.value = "";

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "Passwords do not match.";
    return;
  }

  loading.value = true;

  try {
    const res = await axios.post("http://127.0.0.1:5000/auth/register", {
      name: name.value,
      email: email.value,
      password: password.value,
    });

    const user = res.data.user;
    successMessage.value = "Registration successful! Redirecting...";

    // Save user in localStorage + store
    saveUserToStorage(user);

    // Redirect based on role
    setTimeout(() => {
      if (user.role === "ADMIN") {
        router.push("/admin-dashboard");
      } else {
        router.push("/user-dashboard");
      }
    }, 800);
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

function goToLogin() {
  router.push("/login");
}
</script>

<style scoped>
.card {
  border-radius: 10px;
}
</style>
