import "./css/index.css";

import HomePage from "./home.js";
import LoginPage from "./login.js";
import RegistrationPage from "./register.js";
import SavedBuildingsPage from "./savedBuildings.js";
import SavedMapPage from "./savedMap.js";
import SavedMapsListPage from "./savedMapsList.js";
import UploadPage from "./upload.js";
import UploadedMapPage from "./uploadedMap.js";

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
       <Route exact path="/" element={<HomePage />} />
       <Route exact path="/login" element={<LoginPage />} />
       <Route exact path="/register" element={<RegistrationPage />} />
       <Route exact path="/savedBuildings" element={<SavedBuildingsPage />} />
       <Route exact path="/savedMap" element={<SavedMapPage />} />
       <Route exact path="/savedMapsList" element={<SavedMapsListPage />} />
       <Route exact path="/upload" element={<UploadPage />} />
       <Route exact path="/uploadedMap" element={<UploadedMapPage />} />
      </Routes>  
    </BrowserRouter>
  </React.StrictMode>
);
