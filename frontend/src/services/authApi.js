import api from "./api";

export const registerFarmer = (email, password, fullName) =>
  api
    .post("/auth/register", { email, password, full_name: fullName })
    .then((r) => r.data);

export const login = (email, password) => {
  // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
  const form = new URLSearchParams();
  form.append("username", email); // FastAPI's OAuth2 form always calls it "username"
  form.append("password", password);
  return api
    .post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
    .then((r) => r.data);
};

export const getMyProfile = () => api.get("/auth/me").then((r) => r.data);

export const getMyDevices = () => api.get("/devices/my").then((r) => r.data);

export const getAllDevices = () => api.get("/devices").then((r) => r.data);

export const registerDevice = (deviceId, label, ownerEmail, location) =>
  api
    .post("/devices", { device_id: deviceId, label, owner_email: ownerEmail, location })
    .then((r) => r.data);
