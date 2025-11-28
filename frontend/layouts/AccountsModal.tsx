import { XIcon } from "@/components/icons/XIcon";
import LazyImage from "@/components/LazyImage";
import NavStore from "@/stores/NavStore";
import UserStore from "@/stores/UserStore";
import { Dialog } from "@kobalte/core";
import { createSignal, For, onMount } from "solid-js";

export default function AccountsModal(props: any) {
  const [open, setOpen] = createSignal(false);
  const [accounts, setAccounts] = createSignal<any[]>([]);
  const [, setUser] = UserStore.user;

  const handleFetchAccounts = async () => {
    const accounts_data = await pywebview.api.auth.get_all_accounts();
    setAccounts(accounts_data);
  };

  onMount(handleFetchAccounts);

  const handleAddLogin = async () => {
    const authedUser = await pywebview.api.auth.login();
    if (authedUser) {
      setOpen(false);
      NavStore.isSwitchingAccount[1](true);
      const userInfo = await pywebview.api.user.get_authed_user();
      setUser({
        id: userInfo.id,
        username: userInfo.name,
        displayName: userInfo.displayName,
        imageUrl: userInfo.image,
        robux: userInfo.robux,
      });
      UserStore.resetStore();
      handleFetchAccounts();
      NavStore.goTo("Home");
      NavStore.isSwitchingAccount[1](false);
    }
  };

  const handleSwitchAccount = async (accountId: number) => {
    if (accountId === UserStore.user[0]().id) return;
    const authedUser = await pywebview.api.auth.switch_account(accountId);
    if (authedUser) {
      setOpen(false);
      NavStore.isSwitchingAccount[1](true);
      const userInfo = await pywebview.api.user.get_authed_user();
      setUser({
        id: userInfo.id,
        username: userInfo.name,
        displayName: userInfo.displayName,
        imageUrl: userInfo.image,
        robux: userInfo.robux,
      });
      UserStore.resetStore();
      handleFetchAccounts();
      NavStore.goTo("Home");
      NavStore.isSwitchingAccount[1](false);
    }
  };

  const handleDeleteAccount = async (accountId: number) => {
    await pywebview.api.auth.delete_account(accountId);
    handleFetchAccounts();
  };

  const handleLogout = async () => {
    handleDeleteAccount(UserStore.user[0]().id);
    window.location.reload(); // just reload duhh :P
  };

  return (
    <Dialog.Root open={open()} onOpenChange={setOpen}>
      <Dialog.Trigger {...props} />
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 data-expanded:animate-[overlay-in_0.4s_forwards] animate-[overlay-out_0.4s]" />
        <div class="fixed inset-0 z-50 flex items-center justify-center">
          <Dialog.Content class="z-50 w-md outline-2 outline-white/5 rounded-3xl p-2 bg-neutral-900/80 shadow-2xl data-expanded:animate-[modal-in_0.2s_ease-out] animate-[modal-out_0.2s_ease-out]">
            <p class="text-lg mb-2 text-center text-white/50 py-2">Switch Account</p>
            <div class="flex flex-col max-h-100 overflow-y-auto gap-1">
              <For each={accounts()}>
                {(account) => (
                  <div class="flex-1 relative group">
                    <button
                      onClick={() => handleSwitchAccount(account.id)}
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
                    <button
                      onClick={() => {
                        handleDeleteAccount(account.id);
                      }}
                      class="absolute right-4 top-1/2 -translate-y-1/2 size-8 grid place-items-center rounded-full hover:bg-white/20 bg-white/10 z-10 opacity-0 group-hover:opacity-100 cursor-pointer transition-[background-color,scale,opacity] active:scale-90">
                      <XIcon class="size-4" />
                    </button>
                  </div>
                )}
              </For>

              <div class="flex gap-2 justify-center mt-2">
                <button
                  onClick={handleAddLogin}
                  class="flex-1 flex justify-center gap-0.5 items-center p-1 rounded-2xl bg-blue-500/80 hover:bg-blue-500 cursor-pointer transition-colors">
                  <p class="py-2">Add Account</p>
                </button>
                <button
                  onClick={handleLogout}
                  class="flex-1 flex justify-center gap-0.5 items-center p-1 rounded-2xl bg-white/5 hover:bg-white/10 cursor-pointer transition-colors">
                  <p class="py-2"> Log out</p>
                </button>
              </div>
            </div>
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
