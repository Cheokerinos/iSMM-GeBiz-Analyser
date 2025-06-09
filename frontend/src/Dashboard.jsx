import React, { useState } from "react";
import axios from "axios";
import { embedReport } from "./powerbiEmbed.js";
import Sidebar from "./utilities/Sidebar";


function Dashboard() {
    const [file, setFile] = useState(null);
    const [embedConfig, setEmbedConfig] = useState(null);

    const onUpload = async () => {
        if (!file) {
            alert("Please select a file to upload.");
            return;
        }

        const formData = new FormData();
        form.append("file", file);
        try {
          const response = await axios.post("http://localhost:8000/uploadfile/", formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          });
          console.log("File uploaded:", response.data);
          setEmbedConfig(response.data)
        } catch (error) {
          console.error("Upload failed:", error);
          }
      };
      
        //const { data } = await axios.post("http://localhost:8000/upload", form);
        //setEmbedConfig(data);


    return (
      <div className="flex min-h-screen w-full bg-gray-100">
        <Sidebar/>
        <main className= "flex-1 flex p-4 items-center justify-center">
          <div className="w-full max-w-2xl bg-white rounded-xl shadow-lg p-8 space-y-6">
            <h1 className = "text-3xl font-extrabold text-gray-800 text-center">
              Power BI Tender Dashboard
            </h1>
            <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-4 sm:space-y-0">
              <label className="flex-1 flex items-center space-x-2">
                <input
                  type="file"
                  onChange={e => setFile(e.target.files[0])}
                  className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4
                            file:rounded-lg file:border-0
                            file:text-sm file:font-semibold
                            file:bg-blue-50 file:text-blue-700
                            hover:file:bg-blue-100
                            transition duration-300 ease-in-out"
                />
              </label>
              <button
                onClick={onUpload}
                className="flex-none px-6 py-2 bg-blue-600 text-white font-medium rounded-lg
                          hover:bg-blue-700 disabled:opacity-50 transition duration-300 ease-in-out"
                disabled={!file}
              >
                Upload & Render
              </button>
            </div>
            {embedConfig && (
            <div
              id="reportContainer"
              className="h-[600px] w-full border border-gray-200 rounded-md shadow-inner"
            />
        )}
        </div>
        </main>
    </div>
  );
}

export default Dashboard;