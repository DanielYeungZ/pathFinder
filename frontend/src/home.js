import "./css/home.css";
import React from 'react';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {

    const navigate = useNavigate();

    return (
    <div>
        <h1>AI Indoor Pathfinding App</h1>
        <p>A computer vision-based pathfinding web application.</p>
        {sessionStorage.getItem("token") != null && <input type="button" class="upload" value="Upload a map" onClick={() => {navigate('/upload');}} />}
        {sessionStorage.getItem("token") != null && <br></br>}
        {sessionStorage.getItem("token") == null && <input type="button" class="login" value="Log into account" onClick={() => {navigate('/login');}} />}
        {sessionStorage.getItem("token") == null && <br></br>}
        {sessionStorage.getItem("token") == null && <input type="button" class="register" value="Register an account" onClick={() => {navigate('/register');}} />}
        {sessionStorage.getItem("token") == null && <br></br>}
        {sessionStorage.getItem("token") != null && <input type="button" class="savedmaps" value="See saved maps" onClick={() => {navigate('/savedBuildings', {state:{previous:'/'}})}} />}
    </div>);
};

export default HomePage;

