function updateLogo() {
  const logos = {
    "Civil Engineering": "/static/images/civil.png",
    "Mechanical Engineering": "/static/images/mechanical.png",
    "Electrical Engineering": "/static/images/electrical.png",
    "Computer Engineering": "/static/images/computer.png",
    "Industrial Engineering": "/static/images/industrial.png",
    "Electronics Engineering": "/static/images/electronics.png",
    "Architecture": "/static/images/architecture.png",
    "Aviation": "/static/images/aviation.png"
  };

  const departmentSelect = document.getElementById("department");
  const selectedDept = departmentSelect.value;
  const logo = document.getElementById("department-logo");

  // Update the logo source
  logo.src = logos[selectedDept] || "/static/ceaa_logo.png";

  // Reset any existing custom class
  logo.classList.remove("aviation");

  // Apply 'aviation' class for the aviation logo to resize it
  if (selectedDept === "Aviation") {
    logo.classList.add("aviation");
  }
}