import { createSignal } from "solid-js";

export type Friends = Friend[];
export type Games = Game[];

const user = createSignal({
  id: 0,
  username: "",
  displayName: "",
  imageUrl: "",
  robux: 0,
});

const isLoginLoading = createSignal(true);
const isDataAvailable = createSignal(false);
const isApiAvailable = createSignal(false);
const isFetchingGames = createSignal(false);
const loadingInfo = createSignal("");

const friends = createSignal<Friends>([]);
const gameRecs = createSignal<Games>([]);
const gameCont = createSignal<Games>([]);
const gameFav = createSignal<Games>([]);

const setLoadingInfoWithTimeout = (() => {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (message: string, timeout = 3000) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    loadingInfo[1](message);
    timeoutId = setTimeout(() => {
      loadingInfo[1]("");
      clearTimeout(timeoutId!);
      timeoutId = null;
    }, timeout);
  };
})();

const initializeStorageStore = async () => {
  console.warn("Initializing...");
  while (typeof pywebview === "undefined") {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  isApiAvailable[1](true);

  let lastAccount = null;
  let attempts = 0;
  const maxAttempts = 3;

  loadingInfo[1]("Checking last account");
  while (attempts < maxAttempts) {
    try {
      lastAccount = await pywebview.api.auth.get_last_account();
      if (lastAccount) break;
    } catch (error) {
      console.error(`Attempt ${attempts + 1} failed:`, error);
    }
    attempts++;
    await new Promise((resolve) => setTimeout(resolve, 100)); // Wait before retrying
  }

  if (lastAccount) {
    isLoginLoading[1](true);
    try {
      await pywebview.api.auth.switch_account(lastAccount.id);
      loadingInfo[1]("Fetching data");

      const userInfo = await pywebview.api.user.get_authed_user().catch((error) => {
        console.error("Failed to fetch user data", error);
        setLoadingInfoWithTimeout("Failed to fetch user data");
        isLoginLoading[1](false);
        throw error;
      });

      loadingInfo[1]("Setting up user data");
      user[1]({
        id: userInfo.id,
        username: userInfo.name || "",
        displayName: userInfo.displayName,
        imageUrl: userInfo.image || "",
        robux: userInfo.robux || 0,
      });

      if (userInfo.id !== 0) {
        isLoginLoading[1](false);
        isDataAvailable[1](true);
      }
    } catch (error) {
      console.error("Error during initialization", error);
      setLoadingInfoWithTimeout("Error during initialization");
      isLoginLoading[1](false);
    }
  } else {
    console.log("No last account found after 3 attempts");
    setLoadingInfoWithTimeout("No last account found");
    isLoginLoading[1](false);
  }
};

const resetStore = () => {
  friends[1]([]);
  gameRecs[1]([]);
  gameCont[1]([]);
  gameFav[1]([]);
};

export default {
  user,
  friends,
  gameRecs,
  gameCont,
  gameFav,
  isLoginLoading,
  isDataAvailable,
  isApiAvailable,
  isFetchingGames,
  loadingInfo,
  initializeStorageStore,
  resetStore,
};
