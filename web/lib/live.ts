"use client";
import { useEffect } from "react";

export function useLiveRefresh(onRefresh: () => void) {
  useEffect(() => {
    let socket: WebSocket | null = null;
    let timer: ReturnType<typeof setInterval> | null = null;
    const connect = () => {
      const explicit = process.env.NEXT_PUBLIC_WS_URL;
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      const url = explicit || `${proto}://${window.location.hostname}:8080/ws/live`;
      try {
        socket = new WebSocket(url);
        socket.onmessage = () => onRefresh();
        socket.onerror = () => socket?.close();
      } catch {}
    };
    connect();
    timer = setInterval(onRefresh, 15000);
    return () => { socket?.close(); if (timer) clearInterval(timer); };
  }, [onRefresh]);
}
