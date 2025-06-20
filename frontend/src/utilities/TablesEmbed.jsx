import React, { useEffect, useState } from "react";
import authAxios from "./authAxios";

export default function TablesEmbed({ TableId, params = {} }) {
  const [iframeUrl, setIframeUrl] = useState(null);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId]   = useState(null);
  const [tables, setTables] = useState([]);
  const [interval, setInterval] = useState(null);

  useEffect(() => {
    authAxios.get("/tables")
      .then(({ data }) => {
        setTables(data);
        if (data.length) setSelectedId(data[0].id);
      })
      .catch(err => {
        console.error("Could not load Tables list:", err);
      });
  }, []);


  useEffect(() => {
    if (!selectedId || isNaN(selectedId)) return;
    async function fetchEmbedUrl() {
      try {
        const { data } = await authAxios.post("/embed_table", {
          question_id: selectedId,
          params,
        });
        console.log("Got embed_url:", data.iframe_url);
        setIframeUrl(data.iframe_url);
      } catch (e) {
        console.error("Failed to get embed URL", e);
        setError("Unable to load table");
      }
    }
    fetchEmbedUrl();
    return () => clearInterval(interval);
  }, [selectedId, params]);

  useEffect(() => {
    const intervalMs = 4 * 60 * 1000;
  
    const intervalId = setInterval(() => {
      if (!selectedId || isNaN(selectedId)) return;
  
      authAxios.post("/embed_table", {
        question_id: selectedId,
        params,
      })
      .then(({ data }) => {
        setIframeUrl(data.iframe_url);
      })
      .catch(e => {
        console.error("Failed to refresh embed URL", e);
      });
  
    }, intervalMs);
  
    return () => clearInterval(intervalId);
  }, [selectedId, JSON.stringify(params)]);

  if (error) return <div className="text-red-600">{error}</div>;
  if (!iframeUrl) return <div>Loading Table…</div>;

  return (
    <div className="flex flex-col w-full h-screen">
      {/* Dropdown */}
      <div className="z-10 p-4">
      <select
        value={selectedId ?? ""}
        onChange={e => setSelectedId(Number(e.target.value))}
        className="border p-2 rounded bg-white mb-4"
      >
        {tables && tables.length > 0 ? (
          tables.map(d => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))
        ) : (
          <option disabled>Loading tables...</option>
        )}
      </select>
      </div>
      {/* Iframe */}
      <div className="flex-1">
      {iframeUrl
        ? <iframe
            key={iframeUrl}
            src={iframeUrl}
            className="w-full h-full border-0"
            frameBorder="0"
          />
        : <p>Loading embed…</p>
      }
      </div>
    </div>
  );
}