import { splitProps } from "solid-js";
import type { JSX } from "solid-js/jsx-runtime";
import { cn } from "./Utils";

export default function Button(props: JSX.ButtonHTMLAttributes<HTMLButtonElement>) {
  const [local, rest] = splitProps(props, ["class"]);
  return (
    <button
      class={cn(
        "px-5 py-2 rounded-full hover:bg-white/10 outline-2 outline-transparent outline-offset-3 active:scale-90  hover:outline-white/50 transition-[scale,outline,background-color] ease-out duration-200 group cursor-pointer select-none",
        local.class
      )}
      {...rest}>
      {props.children}
    </button>
  );
}
