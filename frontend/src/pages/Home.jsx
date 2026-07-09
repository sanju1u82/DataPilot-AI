import { useState } from "react";
import Navbar from "../components/Layout/Navbar";
import UploadBox from "../components/Upload/UploadBox";

function Home() {
    const [selectedFile, setSelectedFile] = useState(null);

    const handleFileSelect = (file) => {
        setSelectedFile(file);
    };

    const handleUpload = () => {
        console.log(selectedFile);
    };

    return (
        <>
            <Navbar />

            <div className="container text-center mt-5">

                <h1 className="display-4 fw-bold">
                    DataPilot AI
                </h1>

                <p className="lead">
                    AI-Powered Data Analysis & AutoML Platform
                </p>

                <UploadBox
                    selectedFile={selectedFile}
                    onFileSelect={handleFileSelect}
                    onUpload={handleUpload}
                />

            </div>
        </>
    );
}

export default Home;