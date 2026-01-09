import FriendCard from "@/components/FriendCard";
import UserStore from "@/stores/UserStore";
import { For, Show } from "solid-js";

export default function Friends() {
  const [friends] = UserStore.friends;
  const [isLoading] = UserStore.isLoginLoading;

  return (
    <div class="flex flex-col gap-6 relative z-10 flex-1">
      {/* friends content */}

      <p class="ml-14 text-xl mt-25">Friends ({friends().length})</p>
      <div
        class={`px-14 grid gap-2 mb-10 ${isLoading() ? "opacity-10 pointer-events-none" : ""}`}
        style={{
          "grid-template-columns": "repeat(auto-fit, minmax(350px, 1fr))",
        }}>
        <For each={friends()}>{(friend) => <FriendCard friend={friend} />}</For>
      </div>

      <Show when={isLoading()}>
        <div class="fixed inset-0 size-full flex justify-center items-center flex-col">
          <img src="loadingIcon.png" alt="Loading Icon" class="size-12 animate-spin opacity-30" />
          <p class="text-xs opacity-50 mt-4 h-5">Loading friends...</p>
        </div>
      </Show>
    </div>
  );
}
