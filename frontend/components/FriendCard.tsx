import { createEffect, createSignal, onCleanup, onMount, Show } from "solid-js";
import LazyImage from "./LazyImage";
import { PlayCircleIcon } from "./icons/PlayCircleIcon";
import Button from "./Button";
import { DotsIcon } from "./icons/DotsIcon";
import { WrenchIcon } from "./icons/WrenchIcon";

const FriendCard = ({ friend }: { friend: FriendT }) => {
  const [friendStatus, setFriendStatus] = createSignal(friend?.friendStatus ?? "");
  let cardRef: HTMLDivElement | undefined;
  onMount(() => {
    if (!cardRef) return;

    cardRef.style.visibility = friend?.presence ? "visible" : "hidden";

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

  const handleAddFriend = () => {
    if (!friend) return;
    if (friend.friendStatus === "NotFriends") {
      pywebview.api.friends.send_friend_request(friend.id).then((success) => {
        if (success) {
          friend.friendStatus = "RequestSent";
          setFriendStatus("RequestSent");
        }
      });
    } else if (friend.friendStatus === "RequestReceived") {
      pywebview.api.friends.accept_friend_request(friend.id).then((success) => {
        if (success) {
          friend.friendStatus = "Friends";
          setFriendStatus("Friends");
        }
      });
    } else if (friend.friendStatus === "RequestSent") {
      return;
    }
  };

  const handleJoin = () => {
    if (!friend.id) return;
    pywebview.api.utility.launch_roblox(
      "Play",
      undefined,
      undefined,
      friend.id,
      undefined,
      undefined
    );
  };
  return (
    <div
      ref={cardRef}
      class={`flex flex-col p-3 bg-white/10 rounded-3xl min-h-[124px] max-w-[600px] ${
        friend?.presence ? "" : "animate-pulse"
      }`}>
      <Show when={friend?.presence}>
        <div class="flex gap-3 flex-1 z-20">
          <div class="relative">
            <LazyImage
              class="bg-white/10 size-25 min-w-25 rounded-xl"
              alt="Profile Image"
              src={friend?.image !== "" ? friend.image : "error.svg"}
            />
            <span
              class={`absolute top-2 right-2 size-2 rounded-full bg-neutral-500 ${
                friend?.presence?.type === "online"
                  ? "bg-green-500! drop-shadow-[0_0_5px] drop-shadow-green-500"
                  : ""
              } ${
                friend?.presence?.type === "in_game" || friend?.presence?.type === "in_studio"
                  ? "bg-blue-500! drop-shadow-[0_0_5px] drop-shadow-blue-500"
                  : ""
              }`}
            />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xl font-bold truncate">{friend?.displayName}</p>
            <p class="text-xs flex shrink">
              <span class="opacity-50">@{friend?.name}</span>

              {friend?.presence?.type === "in_game" &&
                friend.presence.place &&
                friend.presence.job && (
                  <span class="text-xs text-blue-500/80 drop-shadow drop-shadow-black/20 flex items-center shrink overflow-hidden">
                    <PlayCircleIcon class="inline ml-1 mr-0.5 size-3 shrink-0" />
                    <span class="truncate">{friend.presence.lastLocation}</span>
                  </span>
                )}

              {friend?.presence?.type === "in_studio" && (
                <span class="text-xs text-blue-500/80 drop-shadow drop-shadow-black/20 flex items-center shrink overflow-hidden">
                  <WrenchIcon class="inline ml-1 mr-0.5 size-3 shrink-0" />
                  <span class="truncate">In Studio</span>
                </span>
              )}
            </p>

            {/* <div class="flex flex-wrap gap-1 mt-2">
                    <div class="px-2 py-1 bg-white/10 text-xs rounded-full">10 Friends</div>
                    <div class="px-2 py-1 bg-white/10 text-xs rounded-full">20 Followers</div>
                    <div class="px-2 py-1 bg-white/10 text-xs rounded-full">30 Following</div>
                  </div> */}
            <div class="flex gap-1 mt-3">
              <Show
                when={
                  friend?.presence?.type === "in_game" &&
                  friend.presence.place &&
                  friend.presence.job
                }>
                <Button
                  class="bg-blue-500/80 flex-1 text-sm outline-0 hover:bg-blue-500"
                  onClick={() => handleJoin()}>
                  Join
                </Button>
              </Show>
              <Show when={friendStatus() !== "Friends"}>
                <Button
                  class="bg-white/10 flex-1 text-sm outline-0 hover:bg-white/20"
                  onClick={handleAddFriend}>
                  {friendStatus() === "NotFriends"
                    ? "Add Friend"
                    : friendStatus() === "RequestSent"
                    ? "Request Sent"
                    : friendStatus() === "RequestReceived"
                    ? "Accept Request"
                    : "Add Friend"}
                </Button>
              </Show>
              {/* <Button class="bg-white/10 text-sm outline-0 hover:bg-white/20 w-9 p-0 grid place-items-center">
                <DotsIcon class="size-4" />
              </Button> */}
            </div>
          </div>
        </div>

        <div class="z-10">{/* <p class="text-sm pt-2">No bio yet</p> */}</div>
      </Show>
    </div>
  );
};

export default FriendCard;
