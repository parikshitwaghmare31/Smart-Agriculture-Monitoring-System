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

export const registerDevice = (deviceId, label, ownerEmail, location, irrigationParams = {}) =>
  api
    .post("/devices", {
      device_id: deviceId,
      label,
      owner_email: ownerEmail,
      location,
      ...irrigationParams,
    })
    .then((r) => r.data);

export const updateDevice = (deviceId, updates) =>
  api.patch(`/devices/${encodeURIComponent(deviceId)}`, updates).then((r) => r.data);

export const deleteDevice = (deviceId) =>
  api.delete(`/devices/${encodeURIComponent(deviceId)}`).then((r) => r.data);

export const getAllUsers = () => api.get("/users").then((r) => r.data);

export const updateUser = (email, updates) =>
  api.patch(`/users/${encodeURIComponent(email)}`, updates).then((r) => r.data);

export const deleteUser = (email) =>
  api.delete(`/users/${encodeURIComponent(email)}`).then((r) => r.data);

// --- Disease classifier ---

export const getDiseaseModelStatus = () => api.get("/disease/status").then((r) => r.data);

export const getDiseaseCrops = () => api.get("/disease/crops").then((r) => r.data);

export const classifyPlantPhoto = (imageFile) => {
  const formData = new FormData();
  formData.append("image", imageFile);
  return api
    .post("/disease/classify", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const getDiseaseClasses = () => api.get("/disease/classes").then((r) => r.data);

export const createDiseaseClass = (payload) =>
  api.post("/disease/classes", payload).then((r) => r.data);

export const updateDiseaseClass = (id, updates) =>
  api.patch(`/disease/classes/${id}`, updates).then((r) => r.data);

export const deleteDiseaseClass = (id) => api.delete(`/disease/classes/${id}`).then((r) => r.data);

export const deployDiseaseModel = (modelFile, classNamesFile, trainingReportFile) => {
  const formData = new FormData();
  formData.append("onnx_model_file", modelFile);
  formData.append("class_names_file", classNamesFile);
  if (trainingReportFile) {
    formData.append("training_report_file", trainingReportFile);
  }
  return api
    .post("/disease/deploy-model", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};
