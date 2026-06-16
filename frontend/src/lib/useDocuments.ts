"use client";

import { useCallback, useEffect, useState } from "react";
import { listDocuments, type Doc } from "./data";

/** Lists the user's documents and polls every 2.5s while any is PENDING. */
export function useDocuments() {
  const [docs, setDocs] = useState<Doc[]>([]);

  const refreshDocs = useCallback(async () => {
    try {
      setDocs(await listDocuments());
    } catch {
      /* ignore transient list errors */
    }
  }, []);

  useEffect(() => {
    refreshDocs();
  }, [refreshDocs]);

  useEffect(() => {
    if (!docs.some((d) => d.status === "PENDING")) return;
    const id = setInterval(refreshDocs, 2500);
    return () => clearInterval(id);
  }, [docs, refreshDocs]);

  return { docs, refreshDocs };
}
