import "./css/map.css";
import React, {useEffect, useState} from 'react';
import axios from "axios";
import { useNavigate, useLocation } from 'react-router-dom';

const SavedMapPage = () => {
    const [image, setImage] = useState(null);
    const [startRoom, setStartRoom] = useState(null);
    const [endRoom, setEndRoom] = useState(null);
    const [hideBoxes, sethideBoxes] = useState(false);
    const [imageSize, setImageSize] = useState({"width":0, "height":0});
    const [originalImageSize, setOriginalImageSize] = useState({"width":0, "height":0});
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const location = useLocation();

    let previous = '/';

    useEffect(() => {
        loadImage();
        window.addEventListener('resize', updateBoxes);

        return () => {
            window.removeEventListener('resize', updateBoxes);
        };
    }, [location.state])

    const loadImage = async () => {
        try{
            const token = sessionStorage.getItem('token');
            const response = await axios.get('https://pathfinder-816282289217.us-central1.run.app/api/image/' + location.state.mapId, {
                headers: {
                    'Authorization': token
                }
            });
            
            setImage(response.data.image);
        }catch(err){
            console.error(err);
        }
    };

    const sortRoomOptions = () => {
        image.anchors.sort((a, b) => {
            let aString = a.tagData.map(t => t.text).join(', ');
            let bString = b.tagData.map(t => t.text).join(', ');
            if(aString < bString){
                return -1;
            }else if(aString > bString){
                return 1;
            }else{
                return 0;
            }
        })
    }

    const updateBoxes = () => {
        let img = document.getElementById('map'); 
        setImageSize({"width":img.width, "height":img.height});
    };

    const handleImageLoad = () => {
        let img = document.getElementById('map'); 
        setImageSize({"width":img.width, "height":img.height});
        setOriginalImageSize({"width":img.naturalWidth, "height":img.naturalHeight});
    };

    const updateDisplayedImage = (url) => {
        let img = document.getElementById('map');
        img.src = url;
    }

    const handleSelectStart = (event) => {
        if(event.target.value === ""){
            setStartRoom(null);
            return;
        }
        //console.log(event.target.value);
        console.log("new start room");
        setStartRoom(JSON.parse(event.target.value));
    }

    const handleSelectEnd = (event) => {
        if(event.target.value === ""){
            setEndRoom(null);
            return;
        }
        //console.log(event.target.value);
        console.log("new destination room");
        setEndRoom(JSON.parse(event.target.value));
    }

    const handleFindPath = async () => {
        if(!startRoom && !endRoom){
            alert("Please select a starting room and a destination room.");
            return;
        }
        
        if(!startRoom){
            alert("Please select a starting room.");
            return;
        }

        if(!endRoom){
            alert("Please select a destination room.");
            return;
        }

        try{
            const token = sessionStorage.getItem('token');
            setLoading(true);
            const response = await axios.post('https://pathfinder-816282289217.us-central1.run.app/api/calculate_path', 
            { 
                "start_point": [parseInt(startRoom.tagData[0].y * originalImageSize.height), parseInt(startRoom.tagData[0].x * originalImageSize.width)],
                "end_point": [parseInt(endRoom.tagData[0].y * originalImageSize.height), parseInt(endRoom.tagData[0].x * originalImageSize.width)],
                "image_id": location.state.mapId
            },{
                headers:{
                    'Authorization':token
                }
            });
            setLoading(false);
            updateDisplayedImage(response.data.path_image_url + "?" + Date.now())
        }catch(err){
            setLoading(false);
            console.error(err);
        }
    }

    if(sessionStorage.getItem('token') == null){
        return <><p>You must be logged in to view this page.</p><a href="/login">Login</a></>;
    }

    if(location.state == null){
        return (<h1>Please enter this page normally.</h1>);
    }else{
        previous = location.state.previous;
    };

    if(image == null){
        return <h1>LOADING SAVED MAP...</h1>
    }

    if(image){
        sortRoomOptions();
    }

    return (
        <div>
            <input type="button" value="Back" onClick={() => navigate("/savedMapsList", {state:{previous:previous, buildingName:location.state.buildingName, buildingId:location.state.buildingId}})} />
            
            <h1>Building: {image.building.name}, Floor: {image.floor < 0 ? "B" : ""}{Math.abs(image.floor)}</h1>
            <div>
                <div>
                    {"From: "}
                    <select onChange={handleSelectStart}>
                        <option value="">Select a starting room</option>
                        {image.anchors.map(anchor => {
                            if(anchor.classType === 'classroom' && anchor.tagData.length > 0){
                                return <option value={JSON.stringify(anchor)}>{anchor.tagData.map(t => t.text).join(', ')}</option>;
                            }
                        })}
                    </select>
                    {" to "}    
                    <select onChange={handleSelectEnd}>
                        <option value="">Select a destination room</option>
                        {image.anchors.map(anchor => {
                            if(anchor.classType === 'classroom' && anchor.tagData.length > 0){
                                return <option value={JSON.stringify(anchor)}>{anchor.tagData.map(t => t.text).join(', ')}</option>;
                            }
                        })}
                    </select>
                </div>

                <div className="mapBox" style={{position:"relative"}}>
                    <img id="map" alt="A map" src={image.url} style={{width:"50%"}} onLoad={handleImageLoad}/>

                    <svg style={{position:"absolute", left:"25%", top:0, width:"50%", height:"100%", pointerEvents: "none"}}>
                    
                    {!hideBoxes && <>{image.anchors.map(anchor => {   
                        if(anchor.classType === 'classroom'){
                            return <rect x={anchor.x * (imageSize.width / originalImageSize.width) - 0.5 * anchor.width * (imageSize.width / originalImageSize.width)} y={anchor.y * (imageSize.height / originalImageSize.height) - 0.5 * anchor.height * (imageSize.height / originalImageSize.height)} width={anchor.width * (imageSize.width / originalImageSize.width)} height={anchor.height * (imageSize.height / originalImageSize.height)} style={{fill:"transparent", stroke:"black", strokeWidth:"2"}} />
                        }
                    })}</>}
                    {startRoom && <rect x={startRoom.x * (imageSize.width / originalImageSize.width) - 0.5 * startRoom.width * (imageSize.width / originalImageSize.width)} y={startRoom.y * (imageSize.height / originalImageSize.height) - 0.5 * startRoom.height * (imageSize.height / originalImageSize.height)} width={startRoom.width * (imageSize.height / originalImageSize.height)} height={startRoom.height * (imageSize.height / originalImageSize.height)} style={{fill:"transparent", stroke:"green", strokeWidth:"2"}} />}
                    {endRoom && <rect x={endRoom.x * (imageSize.width / originalImageSize.width) - 0.5 * endRoom.width * (imageSize.width / originalImageSize.width)} y={endRoom.y * (imageSize.height / originalImageSize.height) - 0.5 * endRoom.height * (imageSize.height / originalImageSize.height)} width={endRoom.width * (imageSize.height / originalImageSize.height)} height={endRoom.height * (imageSize.height / originalImageSize.height)} style={{fill:"transparent", stroke:"red", strokeWidth:"2"}} />}
                    
                    </svg>  
                    
                </div>
            </div>
            <div><input type="checkbox" id="showBoxes" name="showBoxes" onChange={() => {sethideBoxes(!hideBoxes);}} /><label for="showBoxes">Hide unselected boxes</label></div>
            <div>        
                <input className="path" type="button" value="Find Path" onClick={() => {handleFindPath();}} disabled={loading}/>
                <input className="reset" type="button" value="Reset Image" onClick={() => {updateDisplayedImage(image.url)}} disabled={loading}/>
            </div>
        </div>);
};

export default SavedMapPage;

