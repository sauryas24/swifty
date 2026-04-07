function protectPage(allowedRoles) {
  const token = sessionStorage.getItem("token");
  const role = sessionStorage.getItem("userRole");

  if (!token || !allowedRoles.includes(role)) {
    sessionStorage.clear();
    window.location.replace("Select_role_login.html");
  }
}