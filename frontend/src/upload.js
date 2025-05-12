import "./css/upload.css";
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const UploadPage = () => {
    const [file, setFile] = useState(null);
    const [buildings, setBuildings] = useState([]);
    const [buildingName, setBuildingName] = useState('');
    const [floor, setFloor] = useState(null);
    const [validSubmit, setValidSubmit] = useState(false);
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    useEffect(() => {
      loadBuildings();
    }, []);

    const loadBuildings = async () => {
      try{
        const token = sessionStorage.getItem('token');
        const response = await axios.get('https://pathfinder-816282289217.us-central1.run.app/api/buildings', {
          headers: {
            'Authorization': token
          }
        });
        setBuildings(response.data.buildings);
      }catch(err){
        console.error(err);
      }
    };

    const updateValidSubmit = (buildingName, floor, file) => {
      setValidSubmit(buildingName.length > 0 && floor != null && file);
    }

    const updateBuilding = (value) => {
      setBuildingName(value);
      updateValidSubmit(value, floor, file);  
    }

    const updateFloor = (value) => {
      setFloor(value); 
      updateValidSubmit(buildingName, value, file);  
    }

    const handleFileChange = (event) => {
      setFile(event.target.files[0]);
      updateValidSubmit(buildingName, floor, event.target.files[0]);  
    }

    const handleBuildingUpload = async () => {
      try{
        const token = sessionStorage.getItem('token');
        
        const response = await axios.post('https://pathfinder-816282289217.us-central1.run.app/api/building', 
        { 
          "name": buildingName 
        }, 
        { 
          headers:{
            'Authorization':token
          } 
        });
        return response.data.building_id;
    }catch(err){
        console.error(err);
    }
    };

    const handleFileUpload = async (buildingId) => {
        if (file) {
          setLoading(true);
          const formData = new FormData();
          formData.append('file', file);
          formData.append('building_id', buildingId);
          formData.append('type', 'raw');
          formData.append('floor', floor);

          try {
            const token = sessionStorage.getItem('token');
            sessionStorage.setItem("upload_start_time", Date.now());
            const response = await axios.post('https://pathfinder-816282289217.us-central1.run.app/api/upload_image', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': token
                },
            });
            sessionStorage.setItem("image_upload_time", Date.now() - sessionStorage.getItem("upload_start_time"));
            let imageData = JSON.parse(response.data.imageData);

            sessionStorage.setItem('s3_url', response.data.s3_url);
            sessionStorage.setItem('uploaded_image_id', imageData._id.$oid);
            
            navigate('/uploadedMap');

          } catch (error) {
              console.error('Error uploading file:', error);
          }
        }
      };

      const handleSubmit = async () => {
        try{
          let found = false;
          let buildingId = null;
          buildings.forEach(building => {
            if(building.name === buildingName){
              buildingId = building.id;
              found = true;
            }
          });

          if(!found){
            buildingId = await handleBuildingUpload();
          }
          
          await handleFileUpload(buildingId);
        }catch(err){
          console.error(err);
        }
      };

      if(sessionStorage.getItem('token') == null){
        return <><p>You must be logged in to view this page.</p><a href="/login">Login</a></>;
      }

      if(loading){
        return <h1>UPLOADING...</h1>
      }

      return (
        <div>
          <input type="button" value="Back" onClick={() => {navigate('/')}} />
          <p style={{textAlign: 'justify', textJustify: 'inter-word', marginLeft: '2%', marginRight: '2%'}}>Provide a building name, floor number, and an image of the map you want to do pathfinding on. Processing will be slow if the image is too large or contains things that aren't the map. Avoid glare and make sure the image is right-side up to get accurate results!</p>
          <div>
            <span>Building name: </span>
            <input onChange={ev => updateBuilding(ev.target.value)}/>
            <span> </span>
            <span>Floor number: </span>
            <input style={{width:50}}type="number" onChange={ev => updateFloor(ev.target.value)} />
          </div>
          <br></br>
          <div>
            <input type="file" accept="image/png, image/jpeg, image/jpg" onChange={handleFileChange} />
            <br></br>
            <input class="upload" type="button" value="Submit" onClick={handleSubmit} disabled={!validSubmit}/>
          </div>
        </div>
      );
};

export default UploadPage;

