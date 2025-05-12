import "./css/acctSubmit.css";
import React, {useState} from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    const handleClick = async () => {

        if(email === "" || password === ""){
            alert("Please fill out all fields.");
            return;
        }
        
        if(!email.includes('@')){
            alert("Please enter a valid email address.");
            return;
        }

        try{
            setLoading(true);
            const response = await axios.post('https://pathfinder-816282289217.us-central1.run.app/api/user/login', { email, password });
            setLoading(false);
            const { token } = response.data;
            sessionStorage.setItem('token', token);
            if(token){
                navigate('/');
            }else{
                alert("Login failed. Please check your email and password.");
            }
        }catch(err){
            console.error(err);
            setLoading(false);
            if(err.response && err.response.status === 401){
                alert("Invalid email or password.");
            }
        }
    }
    
    return <div>
        <input type="button" value="Back" onClick={() => {navigate('/');}} />
        <h1>LOGIN</h1> 
        <div>
        <span>Email: </span>
        <input onChange={ev => setEmail(ev.target.value)}/>
        </div>
        <div>
        <span>Password: </span>
        <input type="password" onChange={ev => setPassword(ev.target.value)}/>
        </div>
        <div>
        <input class="login" type="button" value="Submit" onClick={handleClick} disabled={loading}/>
        </div> 
    </div>
};

export default LoginPage;

