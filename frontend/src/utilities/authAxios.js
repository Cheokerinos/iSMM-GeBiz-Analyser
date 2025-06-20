import axios from "axios";

const authAxios = axios.create({
  baseURL: "http://localhost:8000",
});

authAxios.interceptors.request.use(config => {
    const access_token = localStorage.getItem("accessToken");
    console.log();
    if (access_token) {
      config.headers.Authorization = `Bearer ${access_token}`;
    }
    return config;
  });
  
  export default authAxios;