import Button from "@/components/Button";
import { DotsIcon } from "@/components/icons/DotsIcon";
import { FavoriteIcon } from "@/components/icons/FavoriteIcon";
import { LikeIcon } from "@/components/icons/LikeIcon";
import { OpenIcon } from "@/components/icons/OpenIcon";
import { ServerIcon } from "@/components/icons/ServerIcon";
import { ShortcutIcon } from "@/components/icons/ShortcutIcon";
import LazyImage from "@/components/LazyImage";
import Pagination from "@/components/Pagination";
import ShortcutModal from "@/layouts/ShortcutModal";
import NavStore from "@/stores/NavStore";
import UserStore from "@/stores/UserStore";
import NumberFmt from "@/utils/NumberFmt";
import { createEffect, createSignal, For, Show } from "solid-js";

// Utility function to transform the resolution in a Roblox CDN URL
function ChangeResolution(url: string, width: number, height: number): string {
  if (!url) return "";
  return url.replace(/\d+\/\d+\/Image/, `${width}/${height}/Image`);
}

export default function Game() {
  const [gameTabData] = NavStore.gameTabData;
  const [serverTab, setServerTab] = createSignal("Public");
  const [publicServers, setPublicServers] = createSignal<Server[]>([]);
  const [privateServers, setPrivateServers] = createSignal<PrivateServer[]>([]);
  const [currentPage, setCurrentPage] = createSignal(1);
  const serversPerPage = 12;
  const [isLoading, setIsLoading] = createSignal(false);
  const [isLastPage, setIsLastPage] = createSignal(false);
  const [currentPlaceId, setCurrentPlaceId] = createSignal<number | null>(null);

  const [isFavorited, setIsFavorited] = createSignal(false);
  const [isVoted, setIsVoted] = createSignal(false);
  const [canVote, setCanVote] = createSignal(false);

  const gameData = gameTabData()?.data;

  createEffect(() => {
    if (!gameData) return;

    const placeId = gameData.placeId;

    setCurrentPlaceId(placeId);
    setIsLoading(true);
    setIsLastPage(false);
    setCurrentPage(1);
    setPublicServers([]);
    setPrivateServers([]);
    setIsFavorited(gameData.isFavoritedByUser);

    // Fetch vote and favorite status
    pywebview.api.games.get_vote_status(gameData.id).then((voteStatus) => {
      setIsVoted(voteStatus.userVote);
      setCanVote(voteStatus.canVote);
    });

    pywebview.api.games.get_servers(placeId, 50).then(async (servers: Server[]) => {
      // Check if game changed during fetch
      if (currentPlaceId() !== placeId) return;

      let allServers = [...servers];

      // Keep fetching until we have enough servers or no more available
      while (allServers.length < serversPerPage && servers.length > 0 && servers[0]?.nextCursor) {
        const moreServers = await pywebview.api.games.get_servers_next_page();
        // Check if game changed during fetch
        if (currentPlaceId() !== placeId) return;
        if (moreServers.length === 0) break;
        allServers = [...allServers, ...moreServers];
        servers = moreServers;
      }

      // Final check before setting state
      if (currentPlaceId() !== placeId) return;

      setPublicServers(allServers);

      // Check if this is the last page
      if (allServers.length < serversPerPage || !servers[0]?.nextCursor) {
        setIsLastPage(true);
      }

      setIsLoading(false);
    });

    pywebview.api.games.get_servers_private(placeId, 50).then(async (servers: PrivateServer[]) => {
      // Check if game changed during fetch
      if (currentPlaceId() !== placeId) return;

      let allServers = [...servers];

      // Keep fetching until we have enough servers or no more available
      while (allServers.length < serversPerPage && servers.length > 0 && servers[0]?.nextCursor) {
        const moreServers = await pywebview.api.games.get_servers_private_next_page();
        // Check if game changed during fetch
        if (currentPlaceId() !== placeId) return;
        if (moreServers.length === 0) break;
        allServers = [...allServers, ...moreServers];
        servers = moreServers;
      }

      // Final check before setting state
      if (currentPlaceId() !== placeId) return;

      setPrivateServers(allServers);
    });
  });

  // Calculate pagination
  const paginatedPublicServers = () => {
    const start = (currentPage() - 1) * serversPerPage;
    const end = start + serversPerPage;
    return publicServers().slice(start, end);
  };

  const paginatedPrivateServers = () => {
    const start = (currentPage() - 1) * serversPerPage;
    const end = start + serversPerPage;
    return privateServers().slice(start, end);
  };

  const handleNextPage = async () => {
    const currentServers = serverTab() === "Public" ? publicServers() : privateServers();
    const nextPageStart = currentPage() * serversPerPage;
    const placeId = currentPlaceId();

    // If we don't have enough servers for the next page and not at last page, fetch more
    if (currentServers.length < nextPageStart + serversPerPage && !isLastPage()) {
      setIsLoading(true);

      if (serverTab() === "Public") {
        let moreServers = await pywebview.api.games.get_servers_next_page();
        // Check if game changed during fetch
        if (currentPlaceId() !== placeId) {
          setIsLoading(false);
          return;
        }

        let allServers = [...publicServers(), ...moreServers];

        // Keep fetching until we have enough or no more available
        while (
          allServers.length < nextPageStart + serversPerPage &&
          moreServers.length > 0 &&
          moreServers[0]?.nextCursor
        ) {
          moreServers = await pywebview.api.games.get_servers_next_page();
          // Check if game changed during fetch
          if (currentPlaceId() !== placeId) {
            setIsLoading(false);
            return;
          }
          if (moreServers.length === 0) break;
          allServers = [...allServers, ...moreServers];
        }

        // Final check before setting state
        if (currentPlaceId() !== placeId) {
          setIsLoading(false);
          return;
        }

        setPublicServers(allServers);

        if (moreServers.length === 0 || !moreServers[0]?.nextCursor) {
          setIsLastPage(true);
        }
      } else {
        let moreServers = await pywebview.api.games.get_servers_private_next_page();
        // Check if game changed during fetch
        if (currentPlaceId() !== placeId) {
          setIsLoading(false);
          return;
        }

        let allServers = [...privateServers(), ...moreServers];

        // Keep fetching until we have enough or no more available
        while (
          allServers.length < nextPageStart + serversPerPage &&
          moreServers.length > 0 &&
          moreServers[0]?.nextCursor
        ) {
          moreServers = await pywebview.api.games.get_servers_private_next_page();
          // Check if game changed during fetch
          if (currentPlaceId() !== placeId) {
            setIsLoading(false);
            return;
          }
          if (moreServers.length === 0) break;
          allServers = [...allServers, ...moreServers];
        }

        // Final check before setting state
        if (currentPlaceId() !== placeId) {
          setIsLoading(false);
          return;
        }

        setPrivateServers(allServers);

        if (moreServers.length === 0 || !moreServers[0]?.nextCursor) {
          setIsLastPage(true);
        }
      }

      setIsLoading(false);
    }

    setCurrentPage(currentPage() + 1);
  };

  const handlePreviousPage = () => {
    if (currentPage() > 1) {
      setCurrentPage(currentPage() - 1);
    }
  };

  // Reset to page 1 when switching tabs
  createEffect(() => {
    serverTab();
    setCurrentPage(1);
  });

  const handleVote = async () => {
    if (!gameData || !canVote()) return;
    const universeId = gameData.id;
    await pywebview.api.games.set_vote(universeId, !isVoted());
    setIsVoted(!isVoted());
  };

  const handleFavorite = async () => {
    if (!gameData) return;
    const universeId = gameData.id;
    await pywebview.api.games.set_favorite(universeId, !isFavorited());
    UserStore.gameFav[1]((prevFavs) => {
      const updatedGame = { ...gameData, isFavoritedByUser: !isFavorited() };
      if (!isFavorited()) {
        return [updatedGame, ...prevFavs];
      } else {
        return prevFavs.filter((game) => game.id !== updatedGame.id);
      }
    });
    UserStore.gameCont[1]((prevCont) => {
      return prevCont.map((game) =>
        game.id === universeId ? { ...game, isFavoritedByUser: !isFavorited() } : game
      );
    });
    UserStore.gameRecs[1]((prevRecs) => {
      return prevRecs.map((game) =>
        game.id === universeId ? { ...game, isFavoritedByUser: !isFavorited() } : game
      );
    });
    setIsFavorited(!isFavorited());
  };

  const handleJoin = ({ jobId, privateId }: { jobId?: string; privateId?: string }) => {
    if (!gameData) return;
    pywebview.api.utility.launch_roblox(
      "Play",
      undefined,
      gameData.placeId,
      undefined,
      jobId ?? undefined,
      privateId ?? undefined
    );
  };

  return (
    <div class="flex flex-col gap-6 relative z-10 flex-1">
      {/* game content */}
      <LazyImage
        src={ChangeResolution(gameData?.thumbnailUrl[0]!, 768, 432) || ""}
        class="h-120 absolute mask-b-to-90%"
      />
      <div class="pt-60 pb-10 px-8 flex flex-col gap-6 relative z-10 max-w-6xl mx-auto w-full">
        <div class="flex gap-8">
          <LazyImage
            src={gameData?.iconUrl || ""}
            class="w-50 aspect-square object-contain bg-white/10 rounded-2xl outline-2 outline-white/30"
          />
          <div class="flex flex-col">
            <p class="text-4xl font-bold text-pretty">{gameData?.name || "Unknown"}</p>
            <p class="text-lg opacity-50">By {gameData?.creator.name || "Unknown"}</p>
            <div class="flex-1 flex gap-2 min-w-lg place-items-end">
              <Button
                onClick={() => handleJoin({})}
                disabled={
                  !gameData?.playability.isPlayable &&
                  gameData?.playability.playabilityStatus !== "PurchaseRequired"
                }
                class="bg-blue-500/80 text-xl flex-1 py-4 h-15 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                {gameData?.playability.playabilityStatus === "PurchaseRequired"
                  ? gameData?.price
                  : "Play"}
              </Button>
              <Button
                onClick={handleFavorite}
                class="bg-white/10 w-15 h-15 flex items-center justify-center">
                <FavoriteIcon
                  class={`${
                    isFavorited() ? "" : "*:fill-none"
                  } [&>path]:stroke-white [&>path]:stroke-2`}
                />
              </Button>
              <Button
                onClick={handleVote}
                disabled={!canVote()}
                class="bg-white/10 w-15 h-15 flex items-center justify-center  disabled:opacity-50 disabled:cursor-not-allowed">
                <LikeIcon
                  class={`${
                    isVoted() ? "" : "*:fill-none"
                  } [&>path]:stroke-white [&>path]:stroke-2`}
                />
              </Button>
              <ShortcutModal data={gameData}>
                <Button class="bg-white/10 w-15 h-15 flex items-center justify-center">
                  <ShortcutIcon />
                </Button>
              </ShortcutModal>
            </div>
          </div>
        </div>

        <div class="flex gap-2">
          <div class="p-4 px-6 bg-white/10 rounded-2xl flex-1">
            <p class="text-xs opacity-50">Visits</p>
            <p class="text-lg font-semibold">{NumberFmt.FormatNumber(gameData?.visits || 0)}</p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-2xl flex-1">
            <p class="text-xs opacity-50">Playing</p>
            <p class="text-lg font-semibold">{NumberFmt.FormatNumber(gameData?.playCount || 0)}</p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-2xl flex-1">
            <p class="text-xs opacity-50">Upvotes</p>
            <p class="text-lg font-semibold">{NumberFmt.FormatNumber(gameData?.upvotes || 0)}</p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-2xl flex-1">
            <p class="text-xs opacity-50">Favorites</p>
            <p class="text-lg font-semibold">
              {NumberFmt.FormatNumber(gameData?.favoritedCount || 0)}
            </p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-2xl flex-1">
            <p class="text-xs opacity-50">Genre</p>
            <p class="text-lg font-semibold">
              {(gameData?.genre ?? "unknown").charAt(0).toUpperCase() +
                (gameData?.genre ?? "unknown").slice(1).split("_")[0]}
            </p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-2xl flex-1">
            <p class="text-xs opacity-50">Created</p>
            <p class="text-lg font-semibold">
              {new Date(gameData?.created || "").toLocaleDateString("en-GB")}
            </p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-2xl flex-1">
            <p class="text-xs opacity-50">Updated</p>
            <p class="text-lg font-semibold">
              {new Date(gameData?.updated || "").toLocaleDateString("en-GB")}
            </p>
          </div>
        </div>

        <p class="whitespace-break-spaces">
          {gameData?.description || "No description available."}
        </p>

        <div class="flex justify-between items-center">
          <p class="text-2xl opacity-50">Servers</p>
          <div class="flex gap-1 justify-center">
            <button
              onClick={handlePreviousPage}
              disabled={currentPage() === 1}
              class="px-4 py-2 bg-white/10 hover:bg-white/15 rounded-full transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed">
              {"<"}
            </button>
            <button
              onClick={handleNextPage}
              disabled={
                isLoading() ||
                (isLastPage() &&
                  (serverTab() === "Public"
                    ? paginatedPublicServers().length < serversPerPage
                    : paginatedPrivateServers().length < serversPerPage))
              }
              class="px-4 py-2 bg-white/10 hover:bg-white/15 rounded-full transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed">
              {">"}
            </button>

            <div class="bg-white/10 rounded-full p-1 flex gap-1 relative">
              <div
                class={`absolute bg-white/10 rounded-full w-16 h-8 top-1 transition-[margin] ease-out duration-300 pointer-events-none ${
                  serverTab() === "Public" ? "" : "ml-17"
                }`}></div>
              <button
                class="py-2 w-16 h-8 text-xs cursor-pointer transition-colors rounded-full"
                onClick={() => setServerTab("Public")}>
                Public
              </button>
              <button
                class="py-2 w-16 h-8 text-xs cursor-pointer transition-colors rounded-full"
                onClick={() => setServerTab("Private")}>
                Private
              </button>
            </div>
          </div>
        </div>
        <div class="min-h-80 flex flex-col justify-between relative">
          <Show when={isLoading()}>
            <div class="size-full flex flex-col justify-center items-center absolute">
              <img
                src="loadingIcon.png"
                alt="Loading Icon"
                class="size-12 animate-spin opacity-30"
              />
              <p class="text-[10px] opacity-50 mt-4 h-5">Looking for servers...</p>
            </div>
          </Show>
          <Show
            when={
              !isLoading() && paginatedPublicServers().length === 0 && serverTab() === "Public"
            }>
            <div class="size-full flex flex-col justify-center items-center absolute">
              <p class="text-[10px] opacity-50 mt-4 h-5">No public servers found.</p>
            </div>
          </Show>
          <Show
            when={
              !isLoading() && paginatedPrivateServers().length === 0 && serverTab() === "Private"
            }>
            <div class="size-full flex flex-col justify-center items-center absolute">
              <p class="text-[10px] opacity-50 mt-4 h-5">
                No private servers found / Private server is disabled
              </p>
            </div>
          </Show>
          <div class={`grid grid-cols-4 gap-2 h-fit ${isLoading() ? "opacity-30" : ""}`}>
            <Show when={serverTab() === "Public"}>
              <For each={paginatedPublicServers()}>
                {(server: Server, index) => (
                  <button
                    onClick={() => handleJoin({ jobId: server.id })}
                    class="p-4 px-6 bg-white/10 hover:bg-white/15 transition-[scale,background-color] duration-300 ease-out rounded-2xl flex-1 group cursor-pointer active:scale-90 relative overflow-hidden h-fit flex flex-col items-start animate-[fadeIn_0.3s_ease-out_forwards] opacity-0 invisible"
                    style={{ "animation-delay": `${index() * 100}ms` }}>
                    <p class="text-left text-xs opacity-50">
                      ID: {server.id.split("-")[1]}-{server.id.split("-")[2]} ({server.playing}/
                      {server.maxPlayers})
                    </p>
                    <div class="flex min-w-10 -space-x-4 mt-2">
                      <For each={server.playerAvatars}>
                        {(avatar, i) => (
                          <LazyImage
                            src={avatar}
                            style={{ "z-index": i() }}
                            class="size-10 border-2 border-white/10 rounded-full bg-neutral-400"
                          />
                        )}
                      </For>
                      <Show when={server.playing > 5}>
                        <p class="bg-neutral-500 p-0.5 px-1.5 h-fit rounded-full text-xs text-center z-10">
                          {server.playing - 5}+
                        </p>
                      </Show>

                      <ServerIcon class="opacity-5 size-30 absolute pointer-events-none -bottom-10 -right-10" />
                    </div>
                  </button>
                )}
              </For>
            </Show>
            <Show when={serverTab() === "Private"}>
              <For each={paginatedPrivateServers()}>
                {(server: PrivateServer, index) => (
                  <button
                    onClick={() => handleJoin({ privateId: server.accessCode })}
                    class="p-4 px-6 bg-white/10 hover:bg-white/15 transition-[scale,background-color] duration-300 ease-out rounded-2xl flex-1 group cursor-pointer active:scale-90 relative overflow-hidden h-fit flex flex-col  items-start animate-[fadeIn_0.3s_ease-out_forwards] opacity-0 invisible"
                    style={{ "animation-delay": `${index() * 100}ms` }}>
                    <p class="text-left text-xs opacity-50">
                      {server.name} ({server.playing}/{server.maxPlayers})
                    </p>
                    <div class="flex min-w-10 -space-x-4 mt-2">
                      <For each={server.playerAvatars}>
                        {(avatar, i) => (
                          <LazyImage
                            src={avatar}
                            style={{ "z-index": i() }}
                            class="size-10 border-2 border-white/10 rounded-full  bg-neutral-400"
                          />
                        )}
                      </For>
                      <Show when={server.playing > 5}>
                        <p class="bg-neutral-500 p-0.5 px-1.5 h-fit rounded-full text-xs text-center z-10">
                          {server.playing - 5}+
                        </p>
                      </Show>

                      <ServerIcon class="opacity-5 size-30 absolute pointer-events-none -bottom-10 -right-10" />
                    </div>

                    <p class="text-left text-[10px] mt-2 opacity-50 truncate">
                      Owned by {server.owner.displayName}
                    </p>
                  </button>
                )}
              </For>
            </Show>
          </div>
        </div>
      </div>
    </div>
  );
}
