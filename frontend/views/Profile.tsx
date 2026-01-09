import GameCard from "@/components/GameCard";
import FriendCard from "@/components/FriendCard";
import Button from "@/components/Button";
import LazyImage from "@/components/LazyImage";
import { UsersIcon } from "@/components/icons/UsersIcon";
import NavStore from "@/stores/NavStore";
import NumberFmt from "@/utils/NumberFmt";
import { createSignal, onMount, For, Show, createEffect } from "solid-js";
import { createStore } from "solid-js/store";
import { PlayCircleIcon } from "@/components/icons/PlayCircleIcon";
import { WrenchIcon } from "@/components/icons/WrenchIcon";
import AvatarRenderer from "@/components/AvatarRenderer";
import UserStore from "@/stores/UserStore";

// Utility function to transform the resolution in a Roblox CDN URL
function ChangeResolution(url: string, width: number, height: number): string {
  if (!url) return "";
  return url
    .replace(/\d+\/\d+\/AvatarHeadshot/, `${width}/${height}/AvatarHeadshot`)
    .replace(/\d+\/\d+\/Image/, `${width}/${height}/Image`);
}

const PaginatedSection = <T extends any>(props: {
  title: string;
  items: T[];
  itemsPerPage: number;
  renderItem: (item: T, index: () => number) => any;
  gridClass?: string;
  isLoading?: boolean;
}) => {
  const [page, setPage] = createSignal(0);

  // reset page when items change
  createEffect(() => {
    props.items;
    setPage(0);
  });

  const totalPages = () => Math.ceil(props.items.length / props.itemsPerPage);
  const currentItems = () =>
    props.items.slice(page() * props.itemsPerPage, (page() + 1) * props.itemsPerPage);

  return (
    <div
      class={`bg-white/5 rounded-3xl p-6 flex flex-col gap-4 h-fit break-inside-avoid ${
        props.isLoading ? "opacity-50" : ""
      }`}>
      <div class="flex justify-between items-center">
        <h3 class="text-xl font-bold opacity-80">
          {props.title}{" "}
          <span class="opacity-50 text-base">({props.isLoading ? "..." : props.items.length})</span>
        </h3>
        <Show when={totalPages() > 1 && !props.isLoading}>
          <div class="flex gap-1.5 flex-wrap justify-end max-w-[50%]">
            <For each={Array(totalPages())}>
              {(_, i) => (
                <button
                  class={`size-2 rounded-full transition-all cursor-pointer ${
                    page() === i() ? "bg-white scale-125" : "bg-white/20 hover:bg-white/40"
                  }`}
                  onClick={() => setPage(i())}
                />
              )}
            </For>
          </div>
        </Show>
      </div>

      <Show when={props.items.length === 0 && !props.isLoading}>
        <div class="p-8 text-center opacity-50 text-sm italic">
          No {props.title.toLowerCase()} found.
        </div>
      </Show>

      <Show when={props.items.length > 0 || props.isLoading}>
        <div class={props.gridClass ?? "grid grid-cols-2 gap-2"}>
          <For each={currentItems()}>{props.renderItem}</For>
        </div>
      </Show>
    </div>
  );
};

export default function Profile() {
  const [userTab] = NavStore.userTabData;
  const [currentUser] = UserStore.user;
  const [user, setUser] = createSignal<{
    id: number;
    name: string;
    displayName: string;
    image: string;
    friendStatus: "Friends" | "NotFriends" | "RequestSent" | "RequestReceived" | "Self";
    presence: {
      type: string;
      place: number | null;
      universe: number | null;
      job: number | null;
      lastLocation: string | null;
    } | null;
    robux?: number;
  } | null>(null);
  const [creations, setCreations] = createSignal<Game[]>([]);
  const [favorites, setFavorites] = createSignal<Game[]>([]);
  const [groups, setGroups] = createSignal<
    {
      id: number;
      name: string;
      memberCount: number;
      rank: number;
      role: string;
      image: string;
    }[]
  >([]);
  const [badges, setBadges] = createSignal<
    { id: number; name: string; description: string; imageUrl: string }[]
  >([]);
  const [socials, setSocials] = createSignal<{
    facebook?: string;
    twitter?: string;
    youtube?: string;
    twitch?: string;
    guilded?: string;
  }>({});
  const [friends, setFriends] = createSignal<FriendT[]>([]);
  const [followers, setFollowers] = createSignal<FriendT[]>([]);
  const [following, setFollowing] = createSignal<FriendT[]>([]);
  const [counts, setCounts] = createSignal<{
    followersCount: number;
    followingCount: number;
    friendCount: number;
  }>({ followersCount: 0, followingCount: 0, friendCount: 0 });
  const [loading, setLoading] = createStore({
    main: false,
    creations: false,
    favorites: false,
    groups: false,
    badges: false,
    socials: false,
    friends: false,
    followers: false,
    following: false,
  });

  createEffect(async () => {
    const tabData = userTab();
    const targetUserId = tabData?.userId;
    const initialData = tabData?.initialData;

    setLoading({
      main: !initialData,
      creations: true,
      favorites: true,
      groups: true,
      badges: true,
      socials: true,
      friends: true,
      followers: true,
      following: true,
    });

    // Reset state when user changes
    if (initialData && targetUserId) {
      setUser({
        id: targetUserId,
        name: initialData.name,
        displayName: initialData.displayName,
        image: initialData.image,
        friendStatus: initialData.friendStatus || "NotFriends", // Default or handle optional
        presence: initialData.presence || null,
      });
    } else {
      setUser(null);
    }

    setCreations([]);
    setFavorites([]);
    setGroups([]);
    setBadges([]);
    setSocials({});
    setFriends([]);
    setFollowers([]);
    setFollowing([]);
    setCounts({ followersCount: 0, followingCount: 0, friendCount: 0 });

    if (!initialData) {
      pywebview.api.user.get_user_info(targetUserId).then((data) => {
        setUser(data);
        setLoading("main", false);
      });
    }

    pywebview.api.user.get_user_creations(targetUserId).then((data) => {
      setCreations(data);
      setLoading("creations", false);
    });

    pywebview.api.user.get_user_favorites(targetUserId).then((data) => {
      setFavorites(data);
      setLoading("favorites", false);
    });

    pywebview.api.user.get_user_groups(targetUserId).then((data) => {
      setGroups(data);
      setLoading("groups", false);
    });

    pywebview.api.user.get_user_badges(targetUserId).then((data) => {
      setBadges(data);
      setLoading("badges", false);
    });

    pywebview.api.user.get_user_social_links(targetUserId).then((data) => {
      setSocials(data);
      setLoading("socials", false);
    });

    pywebview.api.user.get_user_friends(targetUserId).then((data) => {
      setFriends(data);
      setLoading("friends", false);
    });

    pywebview.api.user.get_followers_count(targetUserId!).then((data) => {
      setCounts(data);
    });
  });
  const handleAddFriend = () => {
    const u = user();
    if (!u) return;

    if (u.friendStatus === "NotFriends") {
      pywebview.api.friends.send_friend_request(u.id).then((success) => {
        if (success) {
          setUser({ ...u, friendStatus: "RequestSent" });
        }
      });
    } else if (u.friendStatus === "RequestReceived") {
      pywebview.api.friends.accept_friend_request(u.id).then((success) => {
        if (success) {
          setUser({ ...u, friendStatus: "Friends" });
        }
      });
    } else if (u.friendStatus === "RequestSent") {
      return;
    }
  };

  const handleJoin = () => {
    const u = user();
    if (!u || !u.presence) return;
    NavStore.isLaunchingRoblox[1](true);
    pywebview.api.utility
      .launch_roblox("Play", undefined, undefined, u.id, undefined, undefined)
      .then(() => {
        NavStore.isLaunchingRoblox[1](false);
      });
  };
  return (
    <div class="flex flex-col gap-6 relative z-10 flex-1">
      {/* Background Banner */}
      <div class="h-80 absolute mask-b-to-90% w-full bg-linear-to-t from-black/80 to-transparent z-0 opacity-50"></div>
      <div class="pt-45 pb-10 px-8 flex flex-col gap-2 relative z-10 max-w-6xl mx-auto w-full">
        <AvatarRenderer
          userId={user()!.id}
          class="w-full h-150 z-0 absolute flex left-full -translate-x-2/3 top-0 [&>canvas]:mask-radial-at-center [&>canvas]:mask-radial-to-90% [&>canvas]:mask-x-from-90% [&>canvas]:mask-b-from-90%"
        />
        {/* Header */}
        <div class="flex gap-8">
          <div class="relative w-40 h-40">
            <Show when={user()?.id}>
              <LazyImage
                src={user()?.image}
                class="w-full h-full object-contain rounded-[35px] bg-white/10 outline-2 outline-white/20"
              />
            </Show>
          </div>
          <div class="flex flex-col w-fit z-10">
            <p class="text-4xl font-bold text-pretty">{user()?.displayName || "Loading..."}</p>
            <p class="text-xl">
              <span class="opacity-50">@{user()?.name || "..."}</span>
              <Show when={user()?.presence?.type === "in_game" && user()?.presence?.place}>
                <span class="text-sm text-white/80 drop-shadow drop-shadow-black/20 inline-flex items-center ml-2 bg-blue-500/40 px-2 py-0.5 rounded-full border border-blue-500/50">
                  <PlayCircleIcon class="inline mr-1 size-4 shrink-0" />
                  <span class="truncate">{user()?.presence?.lastLocation}</span>
                </span>
              </Show>
              <Show when={user()?.presence?.type === "in_studio"}>
                <span class="text-sm text-orange-500/80 drop-shadow drop-shadow-black/20 inline-flex items-center ml-2 bg-orange-500/10 px-2 py-0.5 rounded-full border border-orange-500/20">
                  <WrenchIcon class="inline mr-1 size-4 shrink-0" />
                  <span class="truncate">In Studio</span>
                </span>
              </Show>
              <Show when={user()?.presence?.type === "online"}>
                <span class="text-sm text-green-500/80 drop-shadow drop-shadow-black/20 inline-flex items-center ml-2 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">
                  <span class="size-2 rounded-full bg-green-500 mr-2"></span>
                  <span class="truncate">Online</span>
                </span>
              </Show>
            </p>
            <div class="flex gap-2 mt-auto">
              <Show when={user()?.presence?.type === "in_game" && user()?.presence?.place}>
                <Button
                  class="w-fit bg-blue-500/80 text-xl py-4 px-10 h-15 hover:bg-blue-500"
                  onClick={handleJoin}>
                  Join Game
                </Button>
              </Show>

              <Show
                when={
                  user()?.friendStatus &&
                  user()?.friendStatus !== "Friends" &&
                  user()?.id !== currentUser()?.id
                }>
                <Button
                  class="w-fit bg-white/10 text-xl py-4 px-10 h-15 hover:bg-white/20"
                  onClick={handleAddFriend}>
                  {user()?.friendStatus === "NotFriends"
                    ? "Add Friend"
                    : user()?.friendStatus === "RequestSent"
                    ? "Request Sent"
                    : user()?.friendStatus === "RequestReceived"
                    ? "Accept Request"
                    : user()?.friendStatus === "Friends"
                    ? "Unfriend"
                    : "Add Friend"}
                </Button>
              </Show>

              {/* Socials */}
              {/* <Show when={socials().facebook}>
                <a
                  href={socials().facebook}
                  target="_blank"
                  class="text-xs bg-white/10 px-2 py-1 rounded hover:bg-white/20">
                  Facebook
                </a>
              </Show>
              <Show when={socials().twitter}>
                <a
                  href={socials().twitter}
                  target="_blank"
                  class="text-xs bg-white/10 px-2 py-1 rounded hover:bg-white/20">
                  Twitter
                </a>
              </Show>
              <Show when={socials().youtube}>
                <a
                  href={socials().youtube}
                  target="_blank"
                  class="text-xs bg-white/10 px-2 py-1 rounded hover:bg-white/20">
                  YouTube
                </a>
              </Show>
              <Show when={socials().twitch}>
                <a
                  href={socials().twitch}
                  target="_blank"
                  class="text-xs bg-white/10 px-2 py-1 rounded hover:bg-white/20">
                  Twitch
                </a>
              </Show>
              <Show when={socials().guilded}>
                <a
                  href={socials().guilded}
                  target="_blank"
                  class="text-xs bg-white/10 px-2 py-1 rounded hover:bg-white/20">
                  Guilded
                </a>
              </Show> */}
            </div>
          </div>
        </div>

        {/* Stats / Counts */}
        <div class="flex gap-2 flex-wrap w-1/2 mt-4">
          {/* <div class="p-4 px-6 bg-white/10 rounded-3xl flex-1 text-center min-w-[120px]">
            <p class="text-xs opacity-50">Creations</p>
            <p class="text-lg font-semibold">{creations().length}</p>
          </div> */}
          <div class="p-4 px-6 bg-white/10 rounded-3xl flex-1 text-center min-w-[120px]">
            <p class="text-xs opacity-50">Friends</p>
            <p class="text-lg font-semibold">{NumberFmt.FormatNumber(counts().friendCount)}</p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-3xl flex-1 text-center min-w-[120px]">
            <p class="text-xs opacity-50">Followers</p>
            <p class="text-lg font-semibold">{NumberFmt.FormatNumber(counts().followersCount)}</p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-3xl flex-1 text-center min-w-[120px]">
            <p class="text-xs opacity-50">Following</p>
            <p class="text-lg font-semibold">{NumberFmt.FormatNumber(counts().followingCount)}</p>
          </div>
          {/* <div class="p-4 px-6 bg-white/10 rounded-3xl flex-1 text-center min-w-[120px]">
            <p class="text-xs opacity-50">Favorites</p>
            <p class="text-lg font-semibold">{favorites().length}</p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-3xl flex-1 text-center min-w-[120px]">
            <p class="text-xs opacity-50">Groups</p>
            <p class="text-lg font-semibold">{groups().length}</p>
          </div>
          <div class="p-4 px-6 bg-white/10 rounded-3xl flex-1 text-center min-w-[120px]">
            <p class="text-xs opacity-50">Badges</p>
            <p class="text-lg font-semibold">{badges().length}</p>
          </div> */}
        </div>

        {/* Content Masonry Grid */}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 min-h-80 pb-20 relative">
          <div class="flex flex-col gap-2">
            <PaginatedSection
              title="Creations"
              isLoading={loading.creations}
              items={creations()}
              itemsPerPage={4}
              renderItem={(game) => <GameCard game={game} />}
            />

            <PaginatedSection
              title="Favorites"
              isLoading={loading.favorites}
              items={favorites()}
              itemsPerPage={4}
              renderItem={(game) => <GameCard game={game} />}
            />

            <PaginatedSection
              title="Badges"
              isLoading={loading.badges}
              items={badges()}
              itemsPerPage={12}
              gridClass="grid grid-cols-4 gap-2"
              renderItem={(badge, index) => (
                <div
                  class="p-3 bg-white/10 rounded-2xl flex flex-col gap-2 items-center text-center transition-colors animate-[fadeIn_0.3s_ease-out_forwards] opacity-0 invisible group relative"
                  style={{ "animation-delay": `${index() * 30}ms` }}
                  title={badge.description}>
                  <LazyImage src={badge.imageUrl} class="w-20 h-20 object-contain" />
                  <p class="text-xs font-medium leading-tight line-clamp-2">{badge.name}</p>
                </div>
              )}
            />
          </div>

          <div class="flex flex-col gap-2">
            <PaginatedSection
              title="Friends"
              isLoading={loading.friends}
              items={friends()}
              itemsPerPage={6}
              renderItem={(friend, index) => (
                <FriendCard
                  friend={friend}
                  compact
                  className="invisible opacity-0"
                  style={{ "animation-delay": `${index() * 50}ms` }}
                />
              )}
            />

            <PaginatedSection
              title="Groups"
              isLoading={loading.groups}
              items={groups()}
              itemsPerPage={6}
              renderItem={(group, index) => (
                <div
                  class="p-4 bg-white/10 rounded-2xl flex flex-col gap-3 transition-colors animate-[fadeIn_0.3s_ease-out_forwards] opacity-0 invisible"
                  style={{ "animation-delay": `${index() * 50}ms` }}>
                  <div class="flex gap-3 items-center">
                    <LazyImage src={group.image} class="w-16 h-16 rounded-xl bg-black/20" />
                    <div class="flex-1 overflow-hidden">
                      <p class="font-bold truncate" title={group.name}>
                        {group.name}
                      </p>
                      <p class="text-xs opacity-50 truncate" title={group.role}>
                        {group.role}
                      </p>
                      <div class="flex items-center gap-1 mt-1 opacity-50">
                        <UsersIcon class="w-3 h-3" />
                        <p class="text-xs">{NumberFmt.FormatNumber(group.memberCount)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
