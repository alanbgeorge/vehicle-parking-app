// src/userStore.js
import { ref } from "vue";

export const currentUser = ref(null);

// load user from localStorage when app starts
export function loadUserFromStorage() {
  try {
    const raw = localStorage.getItem("vps_user");
    currentUser.value = raw ? JSON.parse(raw) : null;
  } catch (e) {
    console.error("Failed to load user from storage", e);
    currentUser.value = null;
  }
}

export function saveUserToStorage(user) {
  currentUser.value = user;
  localStorage.setItem("vps_user", JSON.stringify(user));
}

export function logoutUser() {
  currentUser.value = null;
  localStorage.removeItem("vps_user");
}
