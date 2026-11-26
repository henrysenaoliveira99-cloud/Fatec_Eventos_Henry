const menuToggle = document.querySelector("#menuToggle");
const mainNav = document.querySelector("#mainNav");
if (menuToggle && mainNav) {
  menuToggle.addEventListener("click", () => mainNav.classList.toggle("nav-open"));
}
document.querySelectorAll(".flash").forEach((message) => {
  window.setTimeout(() => message.classList.add("flash-hide"), 5000);
});