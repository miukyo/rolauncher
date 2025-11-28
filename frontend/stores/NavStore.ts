import { createSignal } from "solid-js";

type Tab = "Home" | "Avatar" | "Friends" | "Creator" | "User" | "Game" | "Search";

const [getCurrentTab, setCurrentTab] = createSignal("Home" as Tab);

const backgroundImage = createSignal<string>("test.jpg");

const getTab = getCurrentTab;
const goTo = (tab: Tab) => {
  if (tab === getTab()) return;
  document.getElementById("content-wrapper")?.scrollTo({ top: 0 });
  setCurrentTab(tab);
};

const gameTabData = createSignal<{ ref: Tab; data: Game }>();
const isSwitchingAccount = createSignal(false);

export default { getTab, goTo, backgroundImage, gameTabData, isSwitchingAccount };
