import { Dialog } from "@kobalte/core";
import { SearchIcon } from "@/components/icons/SearchIcon";
import NavStore from "@/stores/NavStore";
import searchQuery from "@/stores/SearchStore";
import { createEffect, createSignal, For, onCleanup, Show } from "solid-js";

export default function SearchModal(props: any) {
  const [open, setOpen] = createSignal(false);
  const [getSearchQuery, setSearchQuery] = searchQuery;
  const [searchResults, setSearchResults] = createSignal<Array<string>>([]);
  const [selectedIndex, setSelectedIndex] = createSignal(-1);

  let inputRef: HTMLInputElement | undefined;
  let queryString = "";

  const handleSearch = (query: string) => {
    queryString = query;
    if (query.trim() === "") {
      setSearchResults([]);
      setSelectedIndex(-1);
      return;
    }
    pywebview.api.games.search_suggestions(query).then((results) => {
      if (queryString !== query) return;
      setSearchResults(results);
      setSelectedIndex(-1);
    });
  };

  createEffect(() => {
    if (open()) {
      setSearchResults([]);
      setSelectedIndex(-1);
      setTimeout(() => inputRef?.focus(), 50);
    }
  });

  const handleEnter = (query: string) => {
    setSearchQuery(query);
    NavStore.goTo("Search");
    setOpen(false);
  };

  const handleSelect = (e: KeyboardEvent) => {
    if (!open()) return;
    const results = searchResults().slice(0, 5);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (selectedIndex() < results.length - 1) {
        setSelectedIndex(selectedIndex() + 1);
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (selectedIndex() > 0) {
        setSelectedIndex(selectedIndex() - 1);
      } else if (selectedIndex() === 0) {
        setSelectedIndex(-1);
      }
    } else if (e.key === "Enter") {
      if (selectedIndex() >= 0 && selectedIndex() < results.length) {
        handleEnter(results[selectedIndex()]);
      } else {
        handleEnter(queryString);
      }
    }
  };

  createEffect(() => {
    document.addEventListener("keydown", handleSelect);
    onCleanup(() => document.removeEventListener("keydown", handleSelect));
  });

  return (
    <Dialog.Root open={open()} onOpenChange={setOpen}>
      <Dialog.Trigger {...props} />
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50  bg-black/50 data-expanded:animate-[overlay-in_0.4s_forwards] animate-[overlay-out_0.4s]" />
        <div class="fixed inset-0 z-50 flex flex-col items-center pt-30">
          <Dialog.Content class="z-50 flex flex-col items-center data-expanded:animate-[modal-in_0.2s_ease-out] animate-[modal-out_0.2s_ease-out]">
            <div class="flex items-center w-md p-4 bg-neutral-900/80 rounded-full shadow-[0_0_50px] shadow-black/50 outline-2 outline-white/5 relative animate-border-search overflow-hidden">
              <SearchIcon class="opacity-30 -mt-0.5" />
              <input
                ref={inputRef}
                type="text"
                spellcheck="false"
                placeholder="Search games or players..."
                onInput={(e) => handleSearch(e.currentTarget.value)}
                class="bg-transparent outline-none ml-2 flex-1 text-white placeholder-white/50 selection:bg-white/30"
              />
            </div>
            <Show when={searchResults().length > 0}>
              <div class="flex flex-col w-lg items-center bg-neutral-900/80 rounded-3xl shadow-[0_0_50px] shadow-black/50 outline-2 outline-white/5 overflow-hidden p-2 mt-4">
                <For each={searchResults().slice(0, 5)}>
                  {(result, i) => (
                    <button
                      onClick={() => handleEnter(result)}
                      class={`text-white/50 py-3 px-4 hover:bg-white/10 hover:text-white size-full rounded-2xl cursor-pointer text-left transition-colors ${
                        selectedIndex() === i() ? "bg-white/10! text-white!" : ""
                      }`}>
                      {result}
                    </button>
                  )}
                </For>
              </div>
            </Show>
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
