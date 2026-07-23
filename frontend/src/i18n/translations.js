/**
 * Translation strings for the dashboard, login/register, admin panel, and
 * prediction/disease features. Covers the primary farmer-facing and
 * admin-facing UI text. Add new keys here as new strings are introduced —
 * missing keys fall back to the key itself (visible in English) rather
 * than crashing, so partial translation coverage never breaks the app.
 */

const translations = {
  en: {
    // App-wide
    appTitle: "Smart Agriculture Monitoring",
    signOut: "Sign Out",
    adminPanel: "Admin Panel",
    diseaseClassifier: "Disease Classifier",
    myProfile: "My Profile",
    backToDashboard: "← Back to Dashboard",
    language: "Language",

    // Login / Register
    loginTitle: "Sign In",
    loginSubtitle: "Smart Agriculture Monitoring System",
    email: "Email",
    password: "Password",
    signIn: "Sign In",
    signingIn: "Signing in...",
    noAccountYet: "Don't have an account?",
    registerAsFarmer: "Register as a farmer",
    registerTitle: "Farmer Registration",
    registerSubtitle: "Create your account to view your field's sensor data",
    fullName: "Full Name",
    phoneNumber: "Phone Number",
    phoneNumberHint: "Include country code, e.g. +919876543210 — needed for irrigation alerts",
    createAccount: "Create Account",
    creatingAccount: "Creating account...",
    alreadyHaveAccount: "Already have an account?",
    backToLogin: "Back to Sign In",
    registrationSuccess: "Account created! You can now sign in.",
    registrationDeviceNote:
      "After signing in, ask your administrator to register your sensor node and assign it to your account.",

    // Dashboard
    viewingAllDevices: "Viewing: All devices",
    viewingDevice: "Viewing",
    waitingForData: "Waiting for sensor data...",
    live: "Live",
    disconnected: "Disconnected",
    fieldDevice: "Field / Device:",
    allDevices: "All devices",
    noDataYet: "no data yet",
    soilMoisture: "Soil Moisture",
    temperature: "Temperature",
    humidity: "Humidity",
    sensorTrends: "Sensor Trends",
    noDevicesRegisteredAdmin:
      "No devices have been registered yet. Use the Admin Panel to register a sensor node and assign it to a farmer.",
    noDevicesRegisteredFarmer:
      "No sensor nodes are linked to your account yet. Contact your administrator to have your device registered and assigned to you.",
    deviceNoDataYet: "is registered but hasn't sent any readings yet. Once the sensor node powers on and publishes data, it will appear here automatically.",
    lastUpdated: "Last updated",

    // Prediction panel
    irrigationPrediction: "Irrigation Prediction",
    useLatestReading: "Use Latest Reading",
    predictIrrigation: "Predict Irrigation",
    predicting: "Predicting...",
    irrigationRecommended: "💧 Irrigation Recommended",
    noIrrigationNeeded: "✅ No Irrigation Needed",
    totalForYourField: "Total for your",
    field: "field",
    totalPumpRuntime: "Total pump run-time needed: approximately",
    hours: "hours",
    splitAcrossZones: ", split across all zones",
    zonesWarning: "⚠️ Your pump can't cover the whole field at once — split irrigation into",
    zonesShifts: "zones/shifts",
    irrigationDepthNote: "This is a per-square-meter figure. To see the total liters needed for your actual field, ask your administrator to register your field's size for this device.",
    confidence: "Confidence",
    predictionFailed: "Prediction request failed. Is the backend running?",

    // Profile settings
    profileSettings: "Profile Settings",
    saveChanges: "Save Changes",
    saving: "Saving...",
    alertPreferences: "Irrigation Alert Preferences",
    enableAlerts: "Enable irrigation alerts via SMS/WhatsApp",
    alertChannel: "Alert Channel",
    sms: "SMS",
    whatsapp: "WhatsApp",
    both: "Both",
    profileUpdated: "Profile updated successfully.",
    phoneRequiredForAlerts: "A phone number is required to enable alerts.",

    // Disease classifier
    diseaseClassifierSubtitle:
      "Select your crop, upload or take a photo of the plant, and get an instant assessment plus irrigation, fertilizer, and spraying recommendations.",
    crop: "Crop",
    cropOptional: "(optional — helps you organize, not required for prediction)",
    anyNotSure: "Any / Not sure",
    plantPhoto: "Plant Photo",
    analyzePhoto: "Analyze Photo",
    analyzing: "Analyzing...",
    selectPhotoFirst: "Please select or take a photo first.",
    classificationFailed: "Classification failed. Please try again.",
    modelNotSetUp:
      "This feature isn't set up yet — no disease classifier model has been trained and deployed. Ask your administrator to train a model and deploy it via the Admin Panel.",
  },

  mr: {
    // App-wide
    appTitle: "स्मार्ट शेती निरीक्षण",
    signOut: "साइन आउट",
    adminPanel: "प्रशासक पॅनेल",
    diseaseClassifier: "रोग वर्गीकरण",
    myProfile: "माझी प्रोफाइल",
    backToDashboard: "← डॅशबोर्डवर परत जा",
    language: "भाषा",

    // Login / Register
    loginTitle: "साइन इन करा",
    loginSubtitle: "स्मार्ट शेती निरीक्षण प्रणाली",
    email: "ईमेल",
    password: "पासवर्ड",
    signIn: "साइन इन करा",
    signingIn: "साइन इन होत आहे...",
    noAccountYet: "खाते नाही?",
    registerAsFarmer: "शेतकरी म्हणून नोंदणी करा",
    registerTitle: "शेतकरी नोंदणी",
    registerSubtitle: "तुमच्या शेतातील सेन्सर डेटा पाहण्यासाठी खाते तयार करा",
    fullName: "पूर्ण नाव",
    phoneNumber: "फोन नंबर",
    phoneNumberHint: "देश कोडसह लिहा, उदा. +919876543210 — सिंचन सूचनांसाठी आवश्यक",
    createAccount: "खाते तयार करा",
    creatingAccount: "खाते तयार होत आहे...",
    alreadyHaveAccount: "आधीपासून खाते आहे?",
    backToLogin: "साइन इनवर परत जा",
    registrationSuccess: "खाते तयार झाले! आता तुम्ही साइन इन करू शकता.",
    registrationDeviceNote:
      "साइन इन केल्यानंतर, तुमच्या प्रशासकाला तुमचा सेन्सर नोंदणी करून तुमच्या खात्याशी जोडण्यास सांगा.",

    // Dashboard
    viewingAllDevices: "पाहत आहात: सर्व उपकरणे",
    viewingDevice: "पाहत आहात",
    waitingForData: "सेन्सर डेटाची वाट पाहत आहे...",
    live: "लाइव्ह",
    disconnected: "जोडणी तुटली",
    fieldDevice: "शेत / उपकरण:",
    allDevices: "सर्व उपकरणे",
    noDataYet: "अजून डेटा नाही",
    soilMoisture: "जमिनीतील ओलावा",
    temperature: "तापमान",
    humidity: "आर्द्रता",
    sensorTrends: "सेन्सर कल",
    noDevicesRegisteredAdmin:
      "अजून कोणतीही उपकरणे नोंदणीकृत नाहीत. सेन्सर नोंदणी करण्यासाठी आणि शेतकऱ्याला नियुक्त करण्यासाठी प्रशासक पॅनेल वापरा.",
    noDevicesRegisteredFarmer:
      "अजून तुमच्या खात्याशी कोणतेही सेन्सर जोडलेले नाहीत. तुमचे उपकरण नोंदणी करून तुम्हाला नियुक्त करण्यासाठी तुमच्या प्रशासकाशी संपर्क साधा.",
    deviceNoDataYet: "नोंदणीकृत आहे पण अजून कोणताही डेटा पाठवलेला नाही. सेन्सर सुरू होऊन डेटा पाठवल्यावर तो आपोआप इथे दिसेल.",
    lastUpdated: "शेवटचे अद्यतन",

    // Prediction panel
    irrigationPrediction: "सिंचन अंदाज",
    useLatestReading: "नवीनतम रीडिंग वापरा",
    predictIrrigation: "सिंचनाचा अंदाज घ्या",
    predicting: "अंदाज घेत आहे...",
    irrigationRecommended: "💧 सिंचनाची शिफारस",
    noIrrigationNeeded: "✅ सिंचनाची गरज नाही",
    totalForYourField: "तुमच्या शेतासाठी एकूण",
    field: "शेत",
    totalPumpRuntime: "पंप चालवण्याचा एकूण अंदाजे वेळ",
    hours: "तास",
    splitAcrossZones: ", सर्व झोनमध्ये विभागलेले",
    zonesWarning: "⚠️ तुमचा पंप संपूर्ण शेत एकाच वेळी भरू शकत नाही — सिंचन विभागून करा",
    zonesShifts: "झोन/शिफ्टमध्ये",
    irrigationDepthNote: "हा प्रति चौरस मीटर आकडा आहे. तुमच्या शेतासाठी एकूण लिटर पाहण्यासाठी, तुमच्या प्रशासकाला या उपकरणासाठी शेताचा आकार नोंदवण्यास सांगा.",
    confidence: "विश्वासार्हता",
    predictionFailed: "अंदाज विनंती अयशस्वी झाली. बॅकएंड सुरू आहे का?",

    // Profile settings
    profileSettings: "प्रोफाइल सेटिंग्ज",
    saveChanges: "बदल जतन करा",
    saving: "जतन होत आहे...",
    alertPreferences: "सिंचन सूचना प्राधान्ये",
    enableAlerts: "SMS/WhatsApp द्वारे सिंचन सूचना सक्षम करा",
    alertChannel: "सूचना माध्यम",
    sms: "एसएमएस",
    whatsapp: "व्हॉट्सअॅप",
    both: "दोन्ही",
    profileUpdated: "प्रोफाइल यशस्वीरित्या अद्यतनित झाली.",
    phoneRequiredForAlerts: "सूचना सक्षम करण्यासाठी फोन नंबर आवश्यक आहे.",

    // Disease classifier
    diseaseClassifierSubtitle:
      "तुमचे पीक निवडा, रोपाचा फोटो अपलोड करा किंवा काढा, आणि सिंचन, खत आणि फवारणीच्या शिफारशींसह त्वरित मूल्यांकन मिळवा.",
    crop: "पीक",
    cropOptional: "(ऐच्छिक — व्यवस्थित ठेवण्यास मदत करते, अंदाजासाठी आवश्यक नाही)",
    anyNotSure: "कोणतेही / खात्री नाही",
    plantPhoto: "रोपाचा फोटो",
    analyzePhoto: "फोटोचे विश्लेषण करा",
    analyzing: "विश्लेषण होत आहे...",
    selectPhotoFirst: "कृपया आधी फोटो निवडा किंवा काढा.",
    classificationFailed: "वर्गीकरण अयशस्वी झाले. कृपया पुन्हा प्रयत्न करा.",
    modelNotSetUp:
      "हे वैशिष्ट्य अजून सेट केलेले नाही — कोणतेही रोग वर्गीकरण मॉडेल प्रशिक्षित आणि तैनात केलेले नाही. तुमच्या प्रशासकाला मॉडेल प्रशिक्षित करून प्रशासक पॅनेलद्वारे तैनात करण्यास सांगा.",
  },
};

export default translations;
