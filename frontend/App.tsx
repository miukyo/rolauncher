import "@/App.css";
import Home from "@/views/Home";
import UserStore from "./stores/UserStore";
import Login from "./views/Login";
import { createEffect, createSignal, Match, onMount, Show, Switch } from "solid-js";
import { Motion, Presence } from "solid-motionone";
import Friends from "./views/Friends";
import NavStore from "./stores/NavStore";
import HomeLayout from "./layouts/HomeLayout";
import Game from "./views/Game";
import Search from "./views/Search";

function LoginOrHome() {
  const [isLoginLoading] = UserStore.isLoginLoading;
  const [isDataAvailable] = UserStore.isDataAvailable;
  const [isApiAvailable] = UserStore.isApiAvailable;
  const [user] = UserStore.user;
  const [friends, setFriends] = UserStore.friends;
  const [gameRecs, setGameRecs] = UserStore.gameRecs;
  const [gameCont, setGameCont] = UserStore.gameCont;
  const [gameFav, setGameFav] = UserStore.gameFav;
  const [showHome, setShowHome] = createSignal(false);

  createEffect(async () => {
    if (isDataAvailable()) {
      setShowHome(true);
      return;
    }
    await UserStore.initializeStorageStore();
    if (!isLoginLoading() && isDataAvailable()) {
      setShowHome(true);
    } else {
      console.log("User not logged in");
      setShowHome(false);
    }
  });

  createEffect(() => {
    if (user().id && friends().length === 0 && isApiAvailable() && isDataAvailable()) {
      pywebview.api.friends
        .get_authed_friends([0, 1000])
        .then((friends_data) => {
          setFriends(
            friends_data.map((friend) => ({
              ...friend,
              followersCount: 0,
              followingCount: 0,
              friendCount: 0,
              isFollowersFetched: false,
            }))
          );
        })
        .catch((error) => console.error("Failed to fetch friends:", error));
    }
  });

  createEffect(() => {
    if (user().id && gameCont().length === 0 && isApiAvailable() && isDataAvailable()) {
      pywebview.api.games
        .get_authed_continue(15)
        .then((data) => {
          setGameCont(data);
          NavStore.backgroundImage[1]((data[0]?.thumbnailUrl[0] ?? "test.jpg") as string);
        })
        .catch((error) => console.error("Failed to fetch continue games:", error));
    }
  });

  createEffect(() => {
    if (user().id && gameFav().length === 0 && isApiAvailable() && isDataAvailable()) {
      pywebview.api.games
        .get_authed_favorites(50)
        .then((data) => {
          setGameFav(data);
        })
        .catch((error) => console.error("Failed to fetch favorite games:", error));
    }
  });

  createEffect(() => {
    if (user().id && gameRecs().length === 0 && isApiAvailable() && isDataAvailable()) {
      UserStore.isFetchingGames[1](true);
      pywebview.api.games
        .get_authed_recommendations(50)
        .then((data) => {
          setGameRecs(data);
        })
        .catch((error) => console.error("Failed to fetch recommendations:", error));

      for (let i = 1; i < 6; i++) {
        pywebview.api.games
          .get_authed_recommendations_page(i + 1)
          .then((page) => setGameRecs((prev) => [...prev, ...page.flat()]))
          .catch((error) => console.error(`Failed to fetch page ${i + 1}:`, error));
      }

      // idk why im placing it here but whatever :P
      UserStore.isFetchingGames[1](false);
    }
  });

  onMount(() => {
    const handlePresenceUpdate = (event: any) => {
      const presences = event.detail as {
        id: number;
        presence: {
          type: string;
          place: number | null;
          universe: number | null;
          job: number | null;
          lastLocation: string | null;
        };
      }[];
      setFriends((prevFriends) => {
        // Create a map for efficient lookup and to prevent duplicates
        const friendsMap = new Map(prevFriends.map((f) => [f.id, f]));

        // Update existing friends with new presence data
        presences.forEach((p) => {
          const existingFriend = friendsMap.get(p.id);
          if (existingFriend) {
            friendsMap.set(p.id, {
              ...existingFriend,
              presence: p.presence,
            });
          }
        });

        // Convert back to array and sort by presence type
        const updatedFriends = Array.from(friendsMap.values());
        return updatedFriends.sort((a, b) => {
          const order = { in_game: 0, in_studio: 1, online: 2, offline: 3 };
          const aOrder = order[a.presence.type as keyof typeof order] ?? 4;
          const bOrder = order[b.presence.type as keyof typeof order] ?? 4;
          return aOrder - bOrder;
        });
      });
    };

    window.addEventListener("presencesUpdate", handlePresenceUpdate);

    return () => {
      window.removeEventListener("presencesUpdate", handlePresenceUpdate);
    };
  });

  return isDataAvailable() ? (
    <Home />
  ) : (
    <>
      <Presence>
        <Show when={!showHome()}>
          <Motion
            initial={{ opacity: 1, filter: "blur(0)", scale: 1 }}
            exit={{ opacity: 0, filter: "blur(100px)", scale: 2 }}
            transition={{ duration: 1, easing: "ease-out" }}
            class="fixed w-full h-full top-0 left-0 will-change-transform z-100">
            <Login />
          </Motion>
        </Show>
      </Presence>

      <Presence>
        <Show when={showHome()}>
          <Motion
            initial={{ opacity: 0, filter: "blur(50px)", scale: 0.8 }}
            animate={{ opacity: 1, filter: "blur(0)", scale: 1 }}
            transition={{ duration: 0.5, easing: [0.34, 1.56, 0.64, 1] }}
            class="relative w-full h-full top-0 left-0 will-change-transform">
            <Home />
          </Motion>
        </Show>
      </Presence>
    </>
  );
}

function App() {
  return (
    <main class="w-screen h-screen overflow-hidden">
      <HomeLayout>
        <Switch>
          <Match when={NavStore.getTab() === "Home"}>
            <LoginOrHome />
          </Match>
          <Match when={NavStore.getTab() === "Friends"}>
            <Friends />
          </Match>
          <Match when={NavStore.getTab() === "Game"}>
            <Game />
          </Match>
          <Match when={NavStore.getTab() === "Search"}>
            <Search />
          </Match>
        </Switch>
      </HomeLayout>
    </main>
  );
}

export default App;
