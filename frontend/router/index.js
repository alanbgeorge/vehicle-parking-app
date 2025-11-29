// src/router/index.js
import { createRouter, createWebHistory } from "vue-router";

import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import UserDashboard from "../views/UserDashboard.vue";
import SlotAvailability from "../views/SlotAvailability.vue";
import BookingHistoryView from "../views/BookingHistoryView.vue";
import AdminDashboardView from "../views/AdminDashboardView.vue";

// helper to read current user from localStorage
function getCurrentUser() {
  const raw = localStorage.getItem("vps_user");
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch (e) {
    console.error("Bad vps_user in storage", e);
    localStorage.removeItem("vps_user");
    return null;
  }
}

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: LoginView },
  { path: "/register", component: RegisterView },

  {
    path: "/user-dashboard",
    component: UserDashboard,
    meta: { requiresAuth: true, role: "USER" },
  },

  {
    path: "/slots/:id",
    component: SlotAvailability,
    meta: { requiresAuth: true, role: "USER" },
  },

  {
    path: "/history",
    component: BookingHistoryView,
    meta: { requiresAuth: true, role: "USER" },
  },

  {
    path: "/admin-dashboard",
    component: AdminDashboardView,
    meta: { requiresAuth: true, role: "ADMIN" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// ----------------------------------------
// ROUTE GUARD – Role Based Access Control
// ----------------------------------------
router.beforeEach((to, from, next) => {
  const user = getCurrentUser();

  // 1. If route needs login and user is not logged in → go to /login
  if (to.meta.requiresAuth && !user) {
    return next("/login");
  }

  // 2. If route has role restriction, check it
  if (to.meta.role && user) {
    // user.role will be "ADMIN" or "USER" from backend login response
    if (user.role !== to.meta.role) {
      // if wrong role, redirect to correct home page
      if (user.role === "ADMIN") {
        return next("/admin-dashboard");
      } else {
        return next("/user-dashboard");
      }
    }
  }

  // 3. Otherwise allow navigation
  next();
});

export default router;
