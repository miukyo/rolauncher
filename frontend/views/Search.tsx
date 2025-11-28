import Button from "@/components/Button";
import FriendCard from "@/components/FriendCard";
import GameCard from "@/components/GameCard";
import searchQuery from "@/stores/SearchStore";
import { createEffect, createSignal, For, Index, onCleanup, Show } from "solid-js";

const Search = () => {
  const [isLoading, setIsLoading] = createSignal(true);
  const [isFetchingGame, setIsFetchingGame] = createSignal(false);
  const [userResults, setUserResults] = createSignal<Array<FriendT>>([]);
  const [gameResults, setGameResults] = createSignal<Array<Game>>([]);
  const [gameNextPageCursor, setGameNextPageCursor] = createSignal<string | null>("");
  const [expandUserResults, setExpandUserResults] = createSignal(false);

  createEffect(() => {
    setIsLoading(true);
    setUserResults([]);
    setGameResults([]);
    const query = searchQuery[0]();
    pywebview.api.games
      .search_universes(query)
      .then(([next, games]) => {
        setGameNextPageCursor(next);
        setGameResults(games);
      })
      .finally(() => setIsLoading(false));
    pywebview.api.user
      .search_users(query, 100)
      .then(setUserResults)
      .finally(() => setIsLoading(false));
  });

  let observer: IntersectionObserver | undefined;
  let lastObservedElement: HTMLElement | undefined;

  onCleanup(() => {
    if (observer) {
      observer.disconnect();
    }
  });

  const observeLastElement = (el: HTMLElement | undefined) => {
    if (!el) return;
    if (observer && lastObservedElement) {
      observer.unobserve(lastObservedElement);
    }

    if (!observer) {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (
              entry.isIntersecting &&
              gameResults().length > 0 &&
              !isFetchingGame() &&
              gameNextPageCursor()
            ) {
              setIsFetchingGame(true);
              pywebview.api.games
                .search_universes_next_page()
                .then((newGames) => {
                  setGameNextPageCursor(newGames[0]);
                  setGameResults([...gameResults(), ...newGames[1]]);
                })
                .finally(() => {
                  setIsFetchingGame(false);
                });
            }
          });
        },
        { threshold: 0 }
      );
    }

    observer.observe(el);
    lastObservedElement = el;
  };
  return (
    <div class="flex flex-col relative z-10 flex-1">
      {/* friends content */}

      <p class="ml-14 text-xl mt-25 mb-5 text-white/50">
        User search for <span class="text-white">{searchQuery[0]()}</span>
      </p>
      <div
        class={`px-14 grid gap-2 max-h-[390px] overflow-hidden ${
          isLoading() ? "opacity-10 pointer-events-none" : ""
        } ${expandUserResults() ? "max-h-max!" : ""}`}
        style={{
          "grid-template-columns": "repeat(auto-fit, minmax(350px, 1fr))",
        }}>
        <Index each={userResults()}>{(user) => <FriendCard friend={user()} />}</Index>
        <For each={isLoading() ? [...Array(15)] : []}>{(user) => <FriendCard friend={user} />}</For>
      </div>

      <Show when={!isLoading() && userResults().length > 15}>
        <div class="flex justify-center mt-4">
          <Button
            onClick={() => setExpandUserResults(!expandUserResults())}
            class="bg-white/10 text-sm outline-0 hover:bg-white/20">
            {expandUserResults() ? "Show less" : "Show more"}
          </Button>
        </div>
      </Show>

      <p class="ml-14 text-xl my-5 text-white/50">
        Game search for <span class="text-white">{searchQuery[0]()}</span>
      </p>

      <div
        class={`grid gap-3 px-14 mb-10 ${isLoading() ? "opacity-10 pointer-events-none" : ""}`}
        style={{
          "grid-template-columns": "repeat(auto-fit, minmax(250px, 1fr))",
        }}>
        <For each={gameResults().length === 0 ? [...Array(10)] : gameResults()}>
          {(game, i) => (
            <GameCard
              ref={(el) => i() === gameResults().length - 1 && observeLastElement(el)}
              game={game}
            />
          )}
        </For>
        <For each={isFetchingGame() ? [...Array(10)] : []}>
          {(game) => <GameCard game={game} />}
        </For>
      </div>

      <Show when={isLoading()}>
        <div class="fixed inset-0 size-full flex justify-center items-center flex-col">
          <img src="loadingIcon.png" alt="Loading Icon" class="size-12 animate-spin opacity-30" />
          <p class="text-xs opacity-50 mt-4 h-5">Loading...</p>
        </div>
      </Show>
    </div>
  );
};

export default Search;
