function protectPage(allowedRoles) {
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("userRole");

  if (!token || !allowedRoles.includes(role)) {
    localStorage.clear();
    window.location.replace("Select_role_login.html");
  }
}