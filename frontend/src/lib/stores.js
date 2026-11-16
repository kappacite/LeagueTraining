import { writable } from "svelte/store";

// undefined = still loading, null = logged out, object = logged-in user
export const user = writable(undefined);
export const meta = writable({ ddragon_version: "" });
