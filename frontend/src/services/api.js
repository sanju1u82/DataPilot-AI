import axios from "axios";

const API = axios.create({
    baseURL: "https://refactored-space-chainsaw-9796q9gqgqx529x4w-8000.app.github.dev",
});

export const uploadCSV = async (file) => {

    const formData = new FormData();

    formData.append("file", file);

    const response = await API.post(
        "/upload",
        formData,
        {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        }
    );

    return response.data;
};