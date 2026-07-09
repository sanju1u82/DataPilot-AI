function UploadBox({
    selectedFile,
    onFileSelect,
    onUpload
}) {

    return (
        <div className="card shadow p-4 mt-5">

            <h3>Upload Dataset</h3>

            <p>Select a CSV file to begin analysis.</p>

            <input
                type="file"
                className="form-control"
                accept=".csv"
                onChange={(e) => onFileSelect(e.target.files[0])}
            />

            {
                selectedFile && (
                    <p className="mt-3">
                        Selected File:
                        <strong> {selectedFile.name}</strong>
                    </p>
                )
            }

            <button
                className="btn btn-primary mt-3"
                disabled={!selectedFile}
                onClick={onUpload}
            >
                Upload
            </button>

        </div>
    );
}

export default UploadBox;