// Mirror of the backend's puzzle type union: one view per type.
import DecisionView from "./DecisionView.svelte";
import ItemizationView from "./ItemizationView.svelte";

export const views = { decision: DecisionView, itemization: ItemizationView };
