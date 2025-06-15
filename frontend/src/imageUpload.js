import { createRef, useState } from "react"

const UploadBook= (props)=>{
    const [image,setImage]=useState();
    const inputFile= createRef();
    const cleanUp= ()=>{
        URL.revokeObjectURL(image && props.image)
        inputFile.current.value=null;
    };
    const SetImage=(newImage)=>{
        if(image){
            cleanUp();
        }
        _SetImage(newImage);
    };
    const handleOnChange=(event)=>{
        const newImage=event.target.files[0];
        if(newImage){
            setImage(URL.createObjectURL(newImage))
        }
        props.imageUpload(event)
    };
    
}