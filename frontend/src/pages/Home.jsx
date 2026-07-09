import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Layout/Navbar";
import UploadBox from "../components/Upload/UploadBox";
import { uploadCSV } from "../services/api";

function Home() {
    const [selectedFile, setSelectedFile] = useState(null);
    const navigate = useNavigate();
    const handleFileSelect = (file) => {
        setSelectedFile(file);
    };

    const handleUpload = async () => {

    if (!selectedFile) {
        alert("Please select a CSV file.");
        return;
    }

    try {

        const result = await uploadCSV(selectedFile);

        navigate("/dashboard", {
    state: {
        profile: result
    }
});

    } catch (error) {

        console.error(error);

        alert("Upload Failed!");

    }

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