import { createSignal, splitProps, createEffect, onCleanup } from "solid-js";
import { cn } from "./Utils";
import type { JSX } from "solid-js/jsx-runtime";

function TransImage(props: JSX.ImgHTMLAttributes<HTMLImageElement>) {
  const [beforeSrc, setBeforeSrc] = createSignal<string | undefined>(undefined);
  const [currentSrc, setCurrentSrc] = createSignal<string | undefined>(undefined);
  const [showTransition, setShowTransition] = createSignal(true);
  const [isTransitioning, setIsTransitioning] = createSignal(false);
  const [local, rest] = splitProps(props, ["class", "src", "alt"]);

  let pendingSrc: string | undefined = undefined;
  let transitionTimeout: ReturnType<typeof setTimeout> | undefined;

  const applyNewSrc = (newSrc: string) => {
    // Step 1: Set current img to before
    setBeforeSrc(currentSrc());

    // Step 2: Set current img opacity to 0 without transition
    setShowTransition(false);
    setIsTransitioning(true);

    // Clear any existing timeout
    if (transitionTimeout) {
      clearTimeout(transitionTimeout);
    }

    // Step 3: Set the new image url to current img (in next frame)
    requestAnimationFrame(() => {
      setCurrentSrc(newSrc);
    });
  };

  const onImageLoad = () => {
    // Step 4: Transition current image from 0 to 100
    requestAnimationFrame(() => {
      setShowTransition(true);
    });

    // Wait for transition to complete (3000ms duration)
    transitionTimeout = setTimeout(() => {
      setIsTransitioning(false);

      // Apply pending src if there is one
      if (pendingSrc && pendingSrc !== currentSrc()) {
        const nextSrc = pendingSrc;
        pendingSrc = undefined;
        applyNewSrc(nextSrc);
      }
    }, 3000);
  };

  createEffect(() => {
    if (local.src && local.src !== currentSrc()) {
      if (isTransitioning()) {
        // Queue the latest src change
        pendingSrc = local.src;
      } else {
        // Apply immediately if not transitioning
        applyNewSrc(local.src);
      }
    }
  });

  onCleanup(() => {
    if (transitionTimeout) {
      clearTimeout(transitionTimeout);
    }
  });

  return (
    <div class={cn("relative size-full pointer-events-none", local.class)}>
      {beforeSrc() && (
        <img
          draggable="false"
          class={cn(`size-full object-cover`)}
          src={beforeSrc()}
          alt={local.alt}
        />
      )}
      <img
        draggable="false"
        class={cn(
          `absolute top-0 left-0 size-full object-cover`,
          showTransition() ? "transition-opacity duration-3000 opacity-100" : "opacity-0"
        )}
        src={currentSrc()}
        alt={local.alt}
        onLoad={onImageLoad}
        {...rest}
      />
    </div>
  );
}

export default TransImage;
