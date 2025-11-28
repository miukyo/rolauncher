import type { JSX } from "solid-js/jsx-runtime";

export function XIcon(props: JSX.SvgSVGAttributes<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" {...props}>
      <path
        fill="none"
        stroke="#fff"
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="3"
        d="M18 6L6 18M6 6l12 12"
      />
    </svg>
  );
}
