import { createApp } from "vue";
import App from "./App.vue";
import router from "./router/index";
import { loadUserFromStorage } from "./userStore";

// ✅ Bootstrap imports
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

loadUserFromStorage();  // set currentUser before app mounts

createApp(App).use(router).mount("#app");
