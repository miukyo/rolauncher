import "@/App.css";
import Home from "@/views/Home";
import UserStore from "./stores/UserStore";
import Login from "./views/Login";
import { createEffect, createSignal, Match, onMount, Show, Switch, useTransition } from "solid-js";
import { Motion, Presence } from "solid-motionone";
import Friends from "./views/Friends";
import NavStore from "./stores/NavStore";
import HomeLayout from "./layouts/HomeLayout";
import Game from "./views/Game";
import Search from "./views/Search";
import Profile from "./views/Profile";

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

  onMount(async () => {
    if (!isDataAvailable()) {
      await UserStore.initializeStorageStore();
    }

    if (!isLoginLoading() && isDataAvailable()) {
      setShowHome(true);

      if (user().id && isApiAvailable()) {
        try {
          if (friends().length === 0) {
            const friends_data = await pywebview.api.friends.get_authed_friends([0, 1000]);
            setFriends(
              friends_data.map((friend) => ({
                ...friend,
                followersCount: 0,
                followingCount: 0,
                friendCount: 0,
                isFollowersFetched: false,
              }))
            );
          }

          if (gameCont().length === 0) {
            const data = await pywebview.api.games.get_authed_continue(15);
            setGameCont(data);
            NavStore.backgroundImage[1]((data[0]?.thumbnailUrl[0] ?? "test.jpg") as string);
          }

          if (gameFav().length === 0) {
            const data = await pywebview.api.games.get_authed_favorites(50);
            setGameFav(data);
          }

          if (gameRecs().length === 0) {
            const data = await pywebview.api.games.get_authed_recommendations(50);
            setGameRecs(data);

            for (let i = 1; i < 6; i++) {
              try {
                const page = await pywebview.api.games.get_authed_recommendations_page(i + 1);
                setGameRecs((prev) => [...prev, ...page.flat()]);
              } catch (error) {
                console.error(`Failed to fetch page ${i + 1}:`, error);
              }
            }
          }
        } catch (error) {
          console.error("An error occurred while fetching data:", error);
        }
      }
    } else {
      console.log("User not logged in");
      setShowHome(false);
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

  return (
    <>
      <Presence>
        <Switch>
          <Match when={!showHome() && !isDataAvailable()}>
            <Login />
          </Match>

          <Match when={showHome() && isDataAvailable()}>
            <Home />
          </Match>
        </Switch>
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
          <Match when={NavStore.getTab() === "User"}>
            <Profile />
          </Match>
        </Switch>
      </HomeLayout>
    </main>
  );
}

export default App;
