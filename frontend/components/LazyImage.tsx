import { createSignal, splitProps } from "solid-js";
import { cn } from "./Utils";
import type { JSX } from "solid-js/jsx-runtime";

function LazyImage(props: JSX.ImgHTMLAttributes<HTMLImageElement>) {
  const [local, rest] = splitProps(props, ["class", "src", "alt"]);
  const handleLoad = (event: Event) => {
    const img = event.target as HTMLImageElement;
    img.style.opacity = "1";
  };

  return (
    <img
      draggable="false"
      class={cn("size-full object-cover transition-opacity duration-500 opacity-0", local.class)}
      src={local.src}
      alt={local.alt}
      onLoad={handleLoad}
      {...rest}
    />
  );
}

export default LazyImage;
