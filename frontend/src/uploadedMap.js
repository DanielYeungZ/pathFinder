import "./css/map.css";
import React, {useState, useEffect} from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const UploadedMapPage = () => {
    const [image, setImage] = useState(null);
    const [startRoom, setStartRoom] = useState(null);
    const [endRoom, setEndRoom] = useState(null);
    const [hideBoxes, sethideBoxes] = useState(false);
    const [imageSize, setImageSize] = useState({"width":0, "height":0});
    const [originalImageSize, setOriginalImageSize] = useState({"width":0, "height":0});
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    useEffect(() => {
        loadImage();
        window.addEventListener('resize', updateBoxes);

        return () => {
            window.removeEventListener('resize', updateBoxes);
        };
    }, []);

    const loadImage = async () => {
        try{
            const token = sessionStorage.getItem('token');
            sessionStorage.setItem("image_load_start_time", Date.now());
            const response = await axios.get('https://pathfinder-816282289217.us-central1.run.app/api/image/' + sessionStorage.getItem("uploaded_image_id"),{
                headers:{
                    'Authorization':token
                }
            });
            sessionStorage.setItem("image_load_time", Date.now() - sessionStorage.getItem("image_load_start_time"));
            setImage(response.data.image);
        }catch(err){
            console.error(err);
        }
    }

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
            sessionStorage.setItem("path_calculation_start_time", Date.now());
            setLoading(true);
            const response = await axios.post('https://pathfinder-816282289217.us-central1.run.app/api/calculate_path', 
            { 
                "start_point": [parseInt(startRoom.tagData[0].y * originalImageSize.height), parseInt(startRoom.tagData[0].x * originalImageSize.width)],
                "end_point": [parseInt(endRoom.tagData[0].y * originalImageSize.height), parseInt(endRoom.tagData[0].x * originalImageSize.width)],
                "image_id": sessionStorage.getItem("uploaded_image_id")
            },{
                headers:{
                    'Authorization':token
                }
            });
            setLoading(false);
            console.log(response.data);
            sessionStorage.setItem("path_calculation_time", Date.now() - sessionStorage.getItem("path_calculation_start_time"));
            updateDisplayedImage(response.data.path_image_url + "?" + Date.now());
        }catch(err){
            sessionStorage.setItem("path_calculation_time", Date.now() - sessionStorage.getItem("path_calculation_start_time"));
            console.error(err);
            setLoading(false);
        }
    }

    if(sessionStorage.getItem('token') == null){
        return <><p>You must be logged in to view this page.</p><a href="/login">Login</a></>;
    }

    if(image == null){
        return <h1>LOADING UPLOADED IMAGE...</h1>
    }

    if(image){
        sortRoomOptions();
    }

    return (
    <div>
        <input type="button" value="Back" onClick={() => navigate('/upload')} />
        
        <h1>Building: {image.building.name}, Floor: {image.floor < 0 ? "B" : ""}{Math.abs(image.floor)}</h1>
        <div>
            <div>
                {"From: "}
                <select onChange={handleSelectStart}>
                    <option value="">Select a starting room</option>
                    {image.anchors.map(anchor => {
                        if((anchor.classType === 'classroom') && anchor.tagData.length > 0){
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
            <input className="saved" type="button" value="Saved Maps" onClick={() => {navigate('/savedBuildings', {state:{previous:'/uploadedMap'}})}} disabled={loading}/>
        </div>
    </div>);

};

export default UploadedMapPage;

