import Button from "@/components/Button";
import { SearchIcon } from "@/components/icons/SearchIcon";
import NavStore from "@/stores/NavStore";
import UserStore from "@/stores/UserStore";
import { Show, type JSX } from "solid-js";
import SearchModal from "./SearchModal";
import TransImage from "@/components/TransImage";
import AccountsModal from "./AccountsModal";

export default function HomeLayout({ children }: { children: JSX.Element }) {
  const { getTab, goTo } = NavStore;
  const [getUser] = UserStore.user;
  const [isDataAvailable] = UserStore.isDataAvailable;

  return (
    <div class="h-screen bg-cover bg-center bg-no-repeat relative flex flex-col">
      <Show when={isDataAvailable()}>
        <div class="fixed h-30 w-full py-10 px-15 z-50 flex justify-between items-center -left-3">
          <div class="flex gap-4">
            <Button
              class={getTab() === "Home" ? "bg-white/10" : ""}
              onClick={() => {
                goTo("Home");
              }}>
              Home
            </Button>
            <Button
              class={getTab() === "Friends" ? "bg-white/10" : ""}
              onClick={() => {
                goTo("Friends");
              }}>
              Friends
            </Button>
          </div>
          <div class="flex gap-4">
            <SearchModal class="outline-0">
              <Button class="px-2">
                <SearchIcon />
              </Button>
            </SearchModal>
            {/* <Button class="px-2" onClick={() => alert("Notification clicked!")}>
              <BellIcon />
            </Button> */}
            {/* <Button class="px-2" onClick={() => alert("Settings clicked!")}>
              <SettingsIcon />
            </Button> */}
            <AccountsModal class="outline-0">
              <Button class="flex gap-2 items-center pr-3 py-1">
                <p>{getUser().displayName}</p>
                <img
                  src={getUser().imageUrl !== "" ? getUser().imageUrl : "error.svg"}
                  alt="Profile"
                  class="size-8 rounded-full"
                />
              </Button>
            </AccountsModal>
          </div>
        </div>
      </Show>
      <Show when={NavStore.isSwitchingAccount[0]()}>
        <div class="fixed z-1000 inset-0 size-full bg-black/80 backdrop-blur-lg flex flex-col items-center justify-center">
          <img src="loadingIcon.png" alt="Loading Icon" class="size-12 animate-spin opacity-30" />
          <p class="text-[10px] opacity-50 mt-4 h-5">Switching account...</p>
        </div>
      </Show>

      <Show when={NavStore.isLaunchingRoblox[0]()}>
        <div class="fixed z-1000 inset-0 size-full bg-black/80 backdrop-blur-lg flex flex-col items-center justify-center">
          <img src="loadingIcon.png" alt="Loading Icon" class="size-12 animate-spin opacity-30" />
          <p class="text-[10px] opacity-50 mt-4 h-5">Launching Roblox...</p>
        </div>
      </Show>
      <TransImage
        class="absolute w-screen opacity-30 h-screen blur-[5rem]"
        src={NavStore.backgroundImage[0]() || "test.jpg"}
        // src="test.jpg"
        alt="background"
      />
      <div
        id="content-wrapper"
        class={`overflow-y-auto overflow-x-hidden scroll-custom mask-t-from-80% h-screen w-screen transition-opacity duration-300 ease-out`}>
        {children}
      </div>
    </div>
  );
}
