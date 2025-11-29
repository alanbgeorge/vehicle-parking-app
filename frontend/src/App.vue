<script setup>
import { RouterView, RouterLink, useRouter } from "vue-router";
import { computed } from "vue";
import { currentUser, logoutUser } from "./userStore";

const router = useRouter();

const hasUser = computed(() => !!currentUser.value);
const userName = computed(() => currentUser.value?.name || "");
const userRole = computed(() => currentUser.value?.role || "");
const isAdmin = computed(() => currentUser.value?.role === "ADMIN");

function handleLogout() {
  logoutUser();
  router.push("/login");
}
</script>

<template>
  <div style="font-family: Arial, sans-serif;">
    <!-- Header -->
    <header
      style="
        padding: 10px;
        background: #eef2f3;
        border-bottom: 1px solid #ccc;
        display: flex;
        justify-content: space-between;
        align-items: center;
      "
    >
      <h2 style="margin: 0;">Vehicle Parking System</h2>

      <!-- Right side: user info + nav -->
      <div>
        <!-- Logged-in info -->
        <div v-if="hasUser" style="margin-bottom: 4px; text-align: right;">
          Logged in as:
          <strong>{{ userName }}</strong>
          ({{ userRole }})
        </div>

        <!-- Navigation -->
        <nav style="text-align: right;">
          <RouterLink
            v-if="hasUser"
            to="/user-dashboard"
            style="margin-right: 15px;"
          >
            Dashboard
          </RouterLink>

          <RouterLink
            v-if="hasUser"
            to="/history"
            style="margin-right: 15px;"
          >
            My History
          </RouterLink>

          <RouterLink
            v-if="hasUser && isAdmin"
            to="/admin-dashboard"
            style="margin-right: 15px;"
          >
            Admin
          </RouterLink>

          <!-- When NOT logged in, show Login/Register -->
          <RouterLink
            v-if="!hasUser"
            to="/login"
            style="margin-right: 15px;"
          >
            Login
          </RouterLink>
          <RouterLink v-if="!hasUser" to="/register">Register</RouterLink>

          <!-- Logout button -->
          <button
            v-if="hasUser"
            @click="handleLogout"
            style="margin-left: 10px; padding: 4px 10px;"
          >
            Logout
          </button>
        </nav>
      </div>
    </header>

    <!-- Page content -->
    <main style="padding: 20px;">
      <RouterView />
    </main>
  </div>
</template>
