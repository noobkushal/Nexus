"use client";

/** Browser API helper: send the HttpOnly session cookie and keep API calls same-site. */
export const getApiBase = () => {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured) return configured.replace(/\\/$/, "");
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  return `http://${window.location.hostname}:8000`;
};

export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  let target: RequestInfo | URL = input;
  if (typeof input === "string") {
    target = input.replace(/^http:\/\/127\.0\.0\.1:8000/, getApiBase());
  }
  return fetch(target, { ...init, credentials: "include" });
}
