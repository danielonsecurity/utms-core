import { ConfigData } from "../types/config";

export const configApi = {
  getConfig: async (signal?: AbortSignal): Promise<ConfigData> => {
    console.log("Fetching config from /api/config");
    const response = await fetch("/api/config", { signal });
    if (!response.ok) throw new Error("Failed to fetch configuration");
    return response.json();
  },

  updateConfig: async (key: string, value: string): Promise<void> => {
    const response = await fetch(`/api/config/${key}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(value),
    });
    if (!response.ok) throw new Error("Failed to update configuration");
  },

  updateListItem: async (
    key: string,
    index: number,
    value: string,
  ): Promise<void> => {
    const response = await fetch(`/api/config/${key}/${index}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(value),
    });
    if (!response.ok) throw new Error("Failed to update list item");
  },

  addNewListItem: async (key: string): Promise<void> => {
    const response = await fetch(`/api/config/${key}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(""),
    });
    if (!response.ok) throw new Error("Failed to add list item");
  },
};
