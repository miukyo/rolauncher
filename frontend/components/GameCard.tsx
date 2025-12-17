import { createEffect, Show, splitProps } from "solid-js";
import Button from "@/components/Button";
import LazyImage from "@/components/LazyImage";
import { LikeIcon } from "@/components/icons/LikeIcon";
import { UsersIcon } from "@/components/icons/UsersIcon";
import NumberFmt from "@/utils/NumberFmt";
import type { JSX } from "solid-js/jsx-runtime";
import { cn } from "./Utils";
import { onMount, onCleanup } from "solid-js";
import NavStore from "@/stores/NavStore";

function GameCard(props: { game: Game } & JSX.HTMLAttributes<HTMLDivElement>) {
  const [local, rest] = splitProps(props, ["class", "game"]);
  let cardRef: HTMLDivElement | undefined;
  const game_data = local.game;

  onMount(() => {
    if (!cardRef) return;

    cardRef.style.visibility = local.game ? "visible" : "hidden";

    const observer = new IntersectionObserver(
      ([entry]) => {
        cardRef!.style.visibility = entry.isIntersecting ? "visible" : "hidden";
      },
      { rootMargin: "200px" }
    );

    observer.observe(cardRef);

    onCleanup(() => {
      observer.disconnect();
    });
  });

  const gameTabData = NavStore.gameTabData;
  const currentTab = NavStore.getTab;

  return (
    <div
      ref={(el) => (cardRef = el)}
      class={cn("flex flex-col flex-1 max-w-[340px]", local.class)}
      {...rest}>
      <Button
        onClick={() => {
          gameTabData[1]({ ref: currentTab(), data: game_data! });
          NavStore.backgroundImage[1](game_data?.thumbnailUrl[0] ?? "");
          NavStore.goTo("Game");
        }}
        class={`p-0 rounded-xl overflow-hidden hover:drop-shadow-white/20 hover:scale-102 will-change-transform w-full aspect-video bg-white/10 ${
          game_data ? "" : "animate-pulse"
        }`}>
        <Show when={game_data}>
          <LazyImage src={game_data?.thumbnailUrl[0] ?? ""} alt={game_data?.name ?? "Unknown"} />
        </Show>
      </Button>
      <p
        class={`mt-2 text-sm min-h-5 line-clamp-2 truncate text-pretty  ${
          game_data ? "" : "bg-white/10 rounded w-30 animate-pulse min-h-4!"
        }`}>
        {game_data?.name}
      </p>
      <div
        class={`flex gap-1 min-h-4 ${
          game_data ? "" : "bg-white/10 rounded w-15 animate-pulse min-h-3! mt-1"
        }`}>
        <Show when={game_data}>
          <p class="text-xs opacity-50 flex items-center">
            <LikeIcon class="size-3.5 mr-0.5" />
            {game_data
              ? `${((game_data.upvotes / (game_data.upvotes + game_data.downvotes)) * 100).toFixed(
                  0
                )}%`
              : ""}
          </p>
          <p class="text-xs opacity-50 flex items-center">
            <UsersIcon class="size-4 mr-0.5" />
            {game_data ? `${NumberFmt.FormatNumber(game_data.playCount)}` : ""}
          </p>
        </Show>
      </div>
    </div>
  );
}

export default GameCard;
