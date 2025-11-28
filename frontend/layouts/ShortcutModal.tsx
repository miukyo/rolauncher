import LazyImage from "@/components/LazyImage";
import { Dialog } from "@kobalte/core";
import { createSignal, For, onMount } from "solid-js";

export default function ShortcutModal(props: { data?: any; [key: string]: any }) {
  const [open, setOpen] = createSignal(false);
  const [accounts, setAccounts] = createSignal<any[]>([]);

  const handleFetchAccounts = async () => {
    const accounts_data = await pywebview.api.auth.get_all_accounts();
    setAccounts(accounts_data);
  };

  onMount(handleFetchAccounts);

  const handleCreateShortcut = (accountName: string, accountId: number) => {
    if (!props.data) return;
    setOpen(false);
    pywebview.api.utility.create_shortcut(
      props.data.name.replace(/[^\w\s]/gi, ""),
      props.data.placeId,
      accountName,
      accountId,
      props.data.iconUrl
    );
  };

  return (
    <Dialog.Root open={open()} onOpenChange={setOpen}>
      <Dialog.Trigger {...props} />
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 data-expanded:animate-[overlay-in_0.4s_forwards] animate-[overlay-out_0.4s]" />
        <div class="fixed inset-0 z-50 flex items-center justify-center">
          <Dialog.Content class="z-50 w-md outline-2 outline-white/5 rounded-3xl p-2 bg-neutral-900/80 shadow-2xl data-expanded:animate-[modal-in_0.2s_ease-out] animate-[modal-out_0.2s_ease-out] relative">
            <p class="text-lg mb-2 text-center text-white/50 py-2">Create game shortcut for</p>
            <div class="flex flex-col max-h-100 overflow-y-auto gap-1">
              <For each={accounts()}>
                {(account) => (
                  <div class="flex-1 relative group">
                    <button
                      onClick={() => handleCreateShortcut(account.displayName, account.id)}
                      class="w-full flex gap-0.5 items-center p-2 rounded-2xl group-hover:bg-white/10 cursor-pointer transition-[background-color,scale] active:scale-90 bg-white/5">
                      <LazyImage
                        src={account.image !== "" ? account.image : "error.svg"}
                        alt="Profile Image"
                        class="size-18 bg-white/10 rounded-xl"
                      />
                      <div class="flex flex-col ml-4">
                        <p class="text-left text-lg">{account.displayName}</p>
                        <p class="text-left text-xs text-white/50">@{account.name}</p>
                      </div>
                    </button>
                  </div>
                )}
              </For>
            </div>
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
