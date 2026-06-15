"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api, postJson, setAccessToken, setRefresh } from "./api";

export type UserResponse = {
  id: string;
  email: string;
  displayName: string;
  role: string;
};

type TokenResponse = {
  accessToken: string;
  refreshToken: string;
  expiresInSeconds: number;
};

type AuthContextValue = {
  user: UserResponse | null;
  ready: boolean;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function fetchMe(): Promise<UserResponse | null> {
  // api() attaches the access token and, on 401, rotates the refresh token once
  // and retries — so a stored refresh token restores the session on mount.
  const res = await api("/api/users/me");
  if (!res.ok) return null;
  return (await res.json()) as UserResponse;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const refresh =
        typeof window !== "undefined" ? localStorage.getItem("faraday_refresh") : null;
      if (refresh) {
        const me = await fetchMe(); // triggers rotate-on-401 inside api()
        if (!cancelled && me) setUser(me);
      }
      if (!cancelled) setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const applyTokens = async (tokens: TokenResponse) => {
    setAccessToken(tokens.accessToken);
    setRefresh(tokens.refreshToken);
    setUser(await fetchMe());
  };

  const register = async (email: string, password: string, displayName: string) => {
    const tokens = await postJson<TokenResponse>("/api/auth/register", {
      email,
      password,
      displayName,
    });
    await applyTokens(tokens);
  };

  const login = async (email: string, password: string) => {
    const tokens = await postJson<TokenResponse>("/api/auth/login", { email, password });
    await applyTokens(tokens);
  };

  const loginWithGoogle = async (idToken: string) => {
    const tokens = await postJson<TokenResponse>("/api/auth/google", { idToken });
    await applyTokens(tokens);
  };

  const logout = async () => {
    const refresh =
      typeof window !== "undefined" ? localStorage.getItem("faraday_refresh") : null;
    if (refresh) {
      // best-effort: logout returns 204, so postJson's json() parse is allowed to fail
      await postJson("/api/auth/logout", { refreshToken: refresh }).catch(() => {});
    }
    setAccessToken(null);
    setRefresh(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, ready, register, login, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
