import { createSignal, For, Index, Show, onCleanup, onMount, createEffect } from "solid-js";
import UserStore from "@/stores/UserStore";
import GameCard from "@/components/GameCard";
import createEmblaCarousel from "embla-carousel-solid";
import LazyImage from "@/components/LazyImage";
import Button from "@/components/Button";
import Autoplay from "embla-carousel-autoplay";
import NavStore from "@/stores/NavStore";
import UserModal from "@/layouts/UserModal";

function Home() {
  const [playerCarouselRef] = createEmblaCarousel(() => ({ dragFree: true }));
  const [continueCarouselRef, continueCarouselApi] = createEmblaCarousel(
    () => ({ dragFree: false, skipSnaps: true }),
    () => [Autoplay({ stopOnInteraction: false })]
  );
  const [selectedSnapContinue, setSelectedSnapContinue] = createSignal(0);
  const [friends] = UserStore.friends;
  const [gameRecs] = UserStore.gameRecs;
  const [gameCont] = UserStore.gameCont;
  const [gameFav] = UserStore.gameFav;

  const backgroundImage = NavStore.backgroundImage;
  createEffect(() => {
    const api = continueCarouselApi();
    if (api) {
      const handleSelect = () => {
        setSelectedSnapContinue(api.selectedScrollSnap());
        backgroundImage[1](
          (gameCont()[api.selectedScrollSnap()]?.thumbnailUrl[0] ?? "test.jpg") as string
        );
      };

      api.on("select", handleSelect);

      onCleanup(() => {
        api.off("select", handleSelect);
      });
    }
  });

  return (
    <>
      {/* main content */}
      <div class="flex flex-col gap-6 relative z-10 flex-1">
        {/* friends content */}
        <div class="pt-20 flex flex-col gap-6 relative z-10">
          <p class="ml-14 mt-5 -mb-5 text-xl">Friends</p>
          <div
            ref={playerCarouselRef}
            class="embla overflow-hidden mask-l-from-[calc(100%-60px)] mask-r-from-[calc(100%-60px)]">
            <div class="flex gap-3 py-2 items-center embla__container">
              <Index each={friends().length === 0 ? [...Array(15)] : friends().slice(0, 15)}>
                {(friend,i) => (
                  <div  class={`relative ${i === 0 ? "ml-14!" : ""} ${
                      i === 14 ? "mr-14!" : ""
                    } group embla__slide flex-[0_0_auto] max-w-full`}>
                    <Button
                      class={`bg-white/10 rounded-2xl p-0 overflow-hidden size-30 shrink-0 group-hover:scale-105 group-hover:outline-white/50! ${
                        friend() ? "" : "animate-pulse"
                      }`}
                      onClick={() => {
                        NavStore.userTabData[1]({
                          ref: NavStore.getTab(),
                          userId: friend().id,
                          initialData: {
                            name: friend().name,
                            displayName: friend().displayName,
                            image: friend().image,
                            friendStatus: friend().friendStatus,
                            presence: friend().presence,
                          },
                        });
                        NavStore.goTo("User");
                      }}>
                      <Show when={friend()}>
                        <LazyImage
                          src={friend()?.image !== "" ? friend()?.image : "error.svg"}
                          alt={friend()?.displayName ?? "Unknown"}
                        />
                        <span
                          class={`absolute top-2 right-2 size-2 rounded-full bg-neutral-500 ${
                            friend()?.presence?.type === "online"
                              ? "bg-green-500! drop-shadow-[0_0_5px] drop-shadow-green-500"
                              : ""
                          } ${
                            friend()?.presence?.type === "in_game" ||
                            friend()?.presence?.type === "in_studio"
                              ? "bg-blue-500! drop-shadow-[0_0_5px] drop-shadow-blue-500"
                              : ""
                          }`}
                        />
                      </Show>
                    </Button>
                    <p class="font-semibold text-center text-xs truncate h-5 w-30">
                      {friend()?.displayName}
                    </p>
                    <p class="text-center text-[10px] truncate w-30 h-4">
                      {friend()?.presence.type === "in_game" ? friend()?.presence.lastLocation : ""}
                      {friend()?.presence.type === "in_studio" ? "In Studio" : ""}
                    </p>
                  </div>
                )}
              </Index>
            </div>
          </div>
        </div>
        {/* continue */}
        <Show when={gameCont().length > 0}>
          <div class="flex items-center gap-4 ml-14 h-80">
            <p class="font-bold text-6xl text-nowrap z-20">
              Jump <br /> back in!
              <br />
              <span class="text-sm font-normal block opacity-50">Continue where you left off</span>
            </p>
            <div
              ref={continueCarouselRef}
              class="embla overflow-hidden  -ml-50 mask-l-from-[calc(100%-20vw)] mask-r-from-[calc(100%-40vw)] flex-1 h-full">
              <div class="flex gap-3 p-10 embla__container items-center">
                <For each={gameCont().length === 0 ? [...Array(10)] : gameCont()}>
                  {(game, i) => (
                    <GameCard
                      class={`shrink-0 flex-[0_0_auto] w-80 embla__slide transition-[scale,margin,outline] duration-500 ease-out
                      ${
                        selectedSnapContinue() === i()
                          ? "scale-120 mx-10 [&>button]:outline-white/50"
                          : ""
                      }
                      ${i() === 0 ? "ml-54!" : ""} 
                      ${i() === gameCont().length - 1 ? "mr-[30%]" : ""}
                      `}
                      game={game}
                    />
                  )}
                </For>
              </div>
            </div>
          </div>
        </Show>
        {/* fav */}
        <Show when={gameFav().length > 0}>
          <p class="ml-14 mt-5 -mb-2 text-xl opacity-50">Favorites</p>
          <div
            class="grid gap-3 px-14 mb-10"
            style={{
              "grid-template-columns": "repeat(auto-fit, minmax(250px, 1fr))",
            }}>
            <For each={gameFav().length === 0 ? [...Array(6)] : gameFav()}>
              {(game) => <GameCard game={game} />}
            </For>
          </div>
        </Show>

        {/* fyp */}
        <p class="ml-14 mt-5 -mb-2 text-xl opacity-50">For you</p>

        <div
          class="grid gap-3 px-14 mb-10"
          style={{
            "grid-template-columns": "repeat(auto-fit, minmax(250px, 1fr))",
          }}>
          <For each={gameRecs().length === 0 ? [...Array(50)] : gameRecs()}>
            {(game) => <GameCard game={game} />}
          </For>
        </div>
      </div>
    </>
  );
}

export default Home;
