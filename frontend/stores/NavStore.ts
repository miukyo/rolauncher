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
const userTabData = createSignal<{
  ref: Tab;
  userId: number | undefined;
  initialData?: {
    name: string;
    displayName: string;
    image: string;
    friendStatus?: "Friends" | "NotFriends" | "RequestSent" | "RequestReceived" | "Self";
    presence?: {
      type: string;
      place: number | null;
      universe: number | null;
      job: number | null;
      lastLocation: string | null;
    } | null;
  };
}>(); // undefined = authed user
const isSwitchingAccount = createSignal(false);
const isLaunchingRoblox = createSignal(false);

export default {
  getTab,
  goTo,
  backgroundImage,
  gameTabData,
  userTabData,
  isSwitchingAccount,
  isLaunchingRoblox,
};
