document.addEventListener("DOMContentLoaded", function () {
  const path = window.location.pathname;

  const assessmentLink = document.getElementById("assessmentLink");
  const startTestBtn = document.getElementById("startTestBtn");

  // If NOT home page → hide Assessment + Start Test
  if (path !== "/" && !path.includes("index.html")) {
    if (assessmentLink) assessmentLink.style.display = "none";
    if (startTestBtn) startTestBtn.style.display = "none";
  }
});
