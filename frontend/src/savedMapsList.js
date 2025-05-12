import "./css/savedMapsList.css";
import React, {useEffect, useState} from 'react';
import axios from "axios";
import { useNavigate, useLocation } from 'react-router-dom';

const SavedMapsListPage = () => {
    const [maps, setMaps] = useState([]);

    const navigate = useNavigate();
    const location = useLocation();
    let previous = '/';

    useEffect(() => {
        loadMaps();
    }, []);

    const loadMaps = async () => {
        try{
            const token = sessionStorage.getItem('token');

            const response = await axios.get('https://pathfinder-816282289217.us-central1.run.app/api/building/' + location.state.buildingId, {
                headers: {
                    'Authorization': token
                }
            });

            const sortedMaps = response.data.building.images;
            sortedMaps.sort((a, b) => (a.floor > b.floor) ? 1 : -1);
            sortedMaps.forEach(map => {
                if(map.floor < 0){
                    map.floor = "B" + Math.abs(map.floor);
                }
                map.floor = "" + map.floor;
            });
            setMaps(sortedMaps);
        }catch(err){
            console.error(err);
        }   
    }

    const deleteMap = async (imageId) => {
        try{
            const token = sessionStorage.getItem('token');

            await axios.delete('https://pathfinder-816282289217.us-central1.run.app/api/image/' + imageId, {
                headers: {
                    'Authorization': token
                },
            });

            loadMaps();
        }catch(err){
            console.error(err);
        }
    }

    if(sessionStorage.getItem('token') == null){
        return <><p>You must be logged in to view this page.</p><a href="/login">Login</a></>;
    }

    if(maps == null){
        return (<h1>LOADING MAPS...</h1>);
    }

    if(location.state == null){
        return (<h1>ERROR</h1>);
    }else{
        previous = location.state.previous;
    }

    return (
        <div>
            <input type="button" value="Back" onClick={() => {navigate('/savedBuildings', {state:{previous:previous}})}} />
            <h1>{location.state.buildingName} Maps</h1>
            {maps.map(map => {
                return <div class="box" onClick={() => {navigate('/savedMap', {state:{previous:previous, buildingName:location.state.buildingName, buildingId:location.state.buildingId, mapId:map.id}})}}>
                            <h1>Floor {map.floor}</h1>
                            {sessionStorage.getItem("uploaded_image_id") !== map.id ? <input class="delete" type='button' onClick={(event) => {event.stopPropagation(); deleteMap(map.id)}} value="X"/> : "Newly uploaded!"}
                        </div>
                        
            })}
        </div>);

};

export default SavedMapsListPage;