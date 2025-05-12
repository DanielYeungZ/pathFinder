import "./css/savedBuildings.css";
import React, {useState, useEffect} from 'react';
import axios from "axios";
import { useNavigate, useLocation } from 'react-router-dom';

const SavedBuildingsPage = () => {
    const [buildings, setBuildings] = useState(null);

    useEffect(() => {
        loadBuildings();
    }, []);

    const navigate = useNavigate();
    const location = useLocation();
    let previous = '/';
    
    const loadBuildings = async () => {
        try{
            const token = sessionStorage.getItem('token');

            const response = await axios.get('https://pathfinder-816282289217.us-central1.run.app/api/buildings', {
                headers: {
                    'Authorization': token
                },
            });

            const sortedBuildings = response.data.buildings;
            sortedBuildings.sort((a, b) => (a.name.toLowerCase() > b.name.toLowerCase()) ? 1 : -1);
            setBuildings(sortedBuildings);
        }catch(err){
            console.error(err);
        }   
    }

    const deleteBuilding = async (buildingID) => {
        try{
            const token = sessionStorage.getItem('token');

            await axios.delete('https://pathfinder-816282289217.us-central1.run.app/api/building/' + buildingID, {
                headers: {
                    'Authorization': token
                },
            });

            loadBuildings();
        }catch(err){
            console.error(err);
        }
    }

    if(sessionStorage.getItem('token') == null){
        return <><p>You must be logged in to view this page.</p><a href="/login">Login</a></>;
    }

    if(location.state == null){
        return (<h1>ERROR</h1>);
    }else{
        previous = location.state.previous;
    }

    if(buildings == null){
        return (<h1>LOADING BUILDINGS...</h1>);
    }
    
    return (
        <div>
            <input type="button" value="Back" onClick={() => {navigate(previous)}} />
            <h1>BUILDINGS</h1>
            {buildings.length > 0 && buildings.map(building => {
                return <div class="box" onClick={() => navigate('/savedMapsList', {state:{previous:previous, buildingId:building.id, buildingName:building.name}})}>
                            <h1>{building.name}</h1>
                            
                            <input class="delete" type='button' onClick={(event) => {event.stopPropagation(); deleteBuilding(building.id)}} value="X"/>
                        </div>
            })}
        </div>);

};
// Add back in if floor number can be retrieved without loading all the images
// <h2>{building.images.length} floor{building.images.length !== 1 && 's'}</h2>
export default SavedBuildingsPage;

