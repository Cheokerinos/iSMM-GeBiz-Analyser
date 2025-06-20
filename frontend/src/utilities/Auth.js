
export function setToken(token) {
    localStorage.setItem("accessToken", token);
  }
  
  export function getToken() {
    return localStorage.getItem("accessToken");
  }
  
  export function clearToken() {
    localStorage.removeItem("accessToken");
  }

  export function setRefreshToken(refresh_token) {
    localStorage.setItem("refreshToken", refresh_token);
  }

  export function getRefreshToken() {
    return localStorage.getItem("refreshToken");
  }