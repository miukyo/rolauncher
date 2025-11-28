import Button from "@/components/Button";
import UserStore from "@/stores/UserStore";
import { Show } from "solid-js";

export default function Login() {
  const [_, setUser] = UserStore.user;
  const [isLoginLoading, setIsLoginLoading] = UserStore.isLoginLoading;
  const [__, setIsDataAvailable] = UserStore.isDataAvailable;
  const [loadingInfo] = UserStore.loadingInfo;

  const handleLogin = async () => {
    const authedUser = await pywebview.api.auth.login();
    if (authedUser) {
      setIsLoginLoading(true);
      const userInfo = await pywebview.api.user.get_authed_user();
      setUser({
        id: userInfo.id,
        username: userInfo.name,
        displayName: userInfo.displayName,
        imageUrl: userInfo.image,
        robux: userInfo.robux,
      });
      setIsLoginLoading(false);
      setIsDataAvailable(true);
      UserStore.resetStore();
    }
  };
  return (
    <div class="w-screen h-screen fixed inset-0 flex flex-col items-center justify-center">
      {/* <img src="loginBg.jpg" alt="Background" class="fixed w-screen h-screen blur-2xl opacity-30" /> */}
      <img src="logoWhite.png" alt="Logo" class="w-60 mb-8 z-10 fixed" />
      <span class="h-80" />
      <Show when={!isLoginLoading()}>
        <Button
          class="relative overflow-hidden outline-white/50 bg-white/10 drop-shadow-[0_0_20px] text-lg px-8 py-2 font-semibold z-10 hover:scale-110 animate-pulse"
          onClick={handleLogin}>
          Login
        </Button>
      </Show>

      <Show when={isLoginLoading()}>
        <img src="loadingIcon.png" alt="Loading Icon" class="size-12 animate-spin opacity-30" />
      </Show>
      <p class="text-[10px] opacity-50 mt-4 h-5">{loadingInfo()}</p>

      <p class="absolute bottom-8 opacity-50 text-xs text-center">
        You need roblox account to use this launcher.
        <br /> If you don't have one, you can create it on the official{" "}
        <a class="underline" href="https://www.roblox.com/CreateAccount" target="_blank">
          Roblox website
        </a>{" "}
        or on the login pop-up.
      </p>
    </div>
  );
}
