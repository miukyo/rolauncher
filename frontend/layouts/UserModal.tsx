import { Dialog } from "@kobalte/core";
import Button from "@/components/Button";
import { DotsIcon } from "@/components/icons/DotsIcon";
import { PlayCircleIcon } from "@/components/icons/PlayCircleIcon";
import { WrenchIcon } from "@/components/icons/WrenchIcon";
import LazyImage from "@/components/LazyImage";
import UserStore from "@/stores/UserStore";
import { createEffect, createSignal, Show } from "solid-js";

export default function UserModal(props: { data?: any; [key: string]: any }) {
  const [open, setOpen] = createSignal(false);
  const [friends, setFriends] = UserStore.friends;
  const [followers, setFollowers] = createSignal({
    followersCount: props.data?.followersCount ?? 0,
    followingCount: props.data?.followersCount ?? 0,
    friendCount: props.data?.followersCount ?? 0,
  });
  createEffect(async () => {
    if (!open() || !props.data) {
      return;
    }
    setFollowers({
      followersCount: friends().find((f) => f.id === props.data?.id)?.followersCount ?? 0,
      followingCount: friends().find((f) => f.id === props.data?.id)?.followingCount ?? 0,
      friendCount: friends().find((f) => f.id === props.data?.id)?.friendCount ?? 0,
    });

    if (friends().find((f) => f.id === props.data?.id)?.isFollowersFetched) {
      return;
    }

    const followers = await pywebview.api.user.get_followers_count(props.data?.id ?? 0);
    setFriends((prevFriends) =>
      prevFriends.map((friend) =>
        friend.id === props.data?.id
          ? {
              ...friend,
              followersCount: followers.followersCount,
              followingCount: followers.followingCount,
              friendCount: followers.friendCount,
              isFollowersFetched: true,
            }
          : friend
      )
    );

    setFollowers(followers);
  });

  const getAuthenticationTicket = async () => {
    if (!props.data) return "";
    const ticket = await pywebview.api.auth.get_authentication_ticket();
    return ticket;
  };

  const [authTicket, setAuthTicket] = createSignal("");

  createEffect(async () => {
    if (open() && props.data && authTicket() === "") {
      const ticket = await getAuthenticationTicket();
      setAuthTicket(ticket);
    }
  });

  const handleJoin = () => {
    if (!props.data) return;
    pywebview.api.utility.launch_roblox(
      "Play",
      undefined,
      undefined,
      props.data?.id,
      undefined,
      undefined
    );
  };

  return (
    <Dialog.Root open={open()} onOpenChange={(isOpen) => setOpen(isOpen)}>
      <Dialog.Trigger {...props} />
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 data-expanded:animate-[overlay-in_0.4s_forwards] animate-[overlay-out_0.4s]" />
        <div class="fixed inset-0 z-50 grid place-items-center">
          <Dialog.Content class="z-50 flex flex-col min-w-md p-4 bg-neutral-900/80 rounded-3xl shadow-[0_0_50px] shadow-black/50 outline-2 outline-white/5 data-expanded:animate-[modal-in_0.2s_ease-out] animate-[modal-out_0.2s_ease-out] relative">
            <div class="absolute top-0 left-0 w-full z-0">
              {/* <div class="bg-linear-0 from-neutral-900 from-30% to-transparent z-20 absolute inset-0 -bottom-10 rounded-3xl"></div> */}
              <LazyImage
                src={props.data?.imageBust}
                alt={`Profile Background`}
                class="relative h-120 -mt-60 w-full object-cover object-[50%_3rem] pointer-events-none z-10 mask-t-from-80% mask-t-to-90%  mask-radial-[50%_90%] mask-radial-from-80% mask-b-from-70%"
              />
              <LazyImage
                src="avatarBg.webp"
                alt={`Profile Background`}
                class="absolute bottom-0 h-60 w-full object-cover pointer-events-none z-0 rounded-3xl opacity-30! mask-b-from-60%"
              />
            </div>

            <div class="flex gap-4 flex-1 z-20 mt-30">
              <div class="relative">
                <LazyImage
                  class="bg-white/10 size-34 rounded-xl"
                  alt="Profile Image"
                  src={props.data?.image !== "" ? props.data?.image : "error.svg"}
                />
                <span
                  class={`absolute top-2 right-2 size-2 rounded-full bg-neutral-500 ${
                    props.data?.presence?.type === "online"
                      ? "bg-green-500! drop-shadow-[0_0_5px] drop-shadow-green-500"
                      : ""
                  } ${
                    props.data?.presence?.type === "in_game" ||
                    props.data?.presence?.type === "in_studio"
                      ? "bg-blue-500! drop-shadow-[0_0_5px] drop-shadow-blue-500"
                      : ""
                  }`}
                />
              </div>
              <div class="flex-1 w-xs">
                <p class="text-2xl font-bold truncate">{props.data?.displayName}</p>
                <p class="text-sm flex items-center">
                  <span class="opacity-50">@{props.data?.name}</span>
                  {props.data?.presence.type === "in_game" &&
                    props.data?.presence.place &&
                    props.data?.presence.job && (
                      <span class="text-sm text-blue-500/80 flex items-center truncate  overflow-hidden">
                        <PlayCircleIcon class="inline ml-1 mr-0.5 size-4 " />
                        <span class="truncate w-50">{props.data?.presence.lastLocation}</span>
                      </span>
                    )}
                  {props.data?.presence?.type === "in_studio" && (
                    <span class="text-sm text-blue-500/80 drop-shadow drop-shadow-black/20 flex items-center shrink overflow-hidden">
                      <WrenchIcon class="inline ml-1 mr-0.5 size-3 shrink-0" />
                      <span class="truncate">In Studio</span>
                    </span>
                  )}
                </p>

                <div class="flex flex-wrap gap-1 mt-2">
                  <div class="px-2 py-1 bg-white/10 text-xs rounded-full">
                    {followers().friendCount} Friends
                  </div>
                  <div class="px-2 py-1 bg-white/10 text-xs rounded-full">
                    {followers().followersCount} Followers
                  </div>
                  <div class="px-2 py-1 bg-white/10 text-xs rounded-full">
                    {followers().followingCount} Following
                  </div>
                </div>
                <div class="flex gap-1 mt-3">
                  <Show
                    when={
                      props.data?.presence.type === "in_game" &&
                      props.data?.presence.place &&
                      props.data?.presence.job
                    }>
                    <Button
                      class="bg-blue-500/80 flex-1 text-sm outline-0 hover:bg-blue-500"
                      onClick={handleJoin}>
                      Join
                    </Button>
                  </Show>
                  {/* <Button class="bg-white/10 flex-1 text-sm outline-0 hover:bg-white/20">
                    Chat
                  </Button>
                  <Button class="bg-white/10 text-sm outline-0 hover:bg-white/20 px-2">
                    <DotsIcon />
                  </Button> */}
                </div>
              </div>
            </div>
            <div class="z-10">{/* <p class="text-sm pt-2">No bio yet</p> */}</div>
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
