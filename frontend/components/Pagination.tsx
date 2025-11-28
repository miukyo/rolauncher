import { For, Show } from "solid-js";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination(props: PaginationProps) {
  // Calculate visible page numbers with ellipsis
  const visiblePages = () => {
    const total = props.totalPages;
    const current = props.currentPage;
    const pages: (number | string)[] = [];

    if (total <= 7) {
      // Show all pages if 7 or fewer
      return Array.from({ length: total }, (_, i) => i + 1);
    }

    // Always show first page
    pages.push(1);

    if (current > 3) {
      pages.push("...");
    }

    // Show pages around current page
    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (current < total - 2) {
      pages.push("...");
    }

    // Always show last page
    pages.push(total);

    return pages;
  };

  return (
    <Show when={props.totalPages > 1}>
      <div class="flex justify-center items-center gap-2 mt-4">
        <button
          class="px-4 py-2 bg-white/10 hover:bg-white/15 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          onClick={() => props.onPageChange(props.currentPage - 1)}
          disabled={props.currentPage === 1}>
          Previous
        </button>

        <div class="flex gap-1">
          <For each={visiblePages()}>
            {(page) => (
              <Show
                when={typeof page === "number"}
                fallback={<span class="size-10 text-white/50 grid place-items-center">...</span>}>
                <button
                  class={`size-10 rounded-lg transition-colors ${
                    props.currentPage === page
                      ? "bg-blue-500 text-white"
                      : "bg-white/10 hover:bg-white/15"
                  }`}
                  onClick={() => props.onPageChange(page as number)}>
                  {page}
                </button>
              </Show>
            )}
          </For>
        </div>

        <button
          class="px-4 py-2 bg-white/10 hover:bg-white/15 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          onClick={() => props.onPageChange(props.currentPage + 1)}
          disabled={props.currentPage === props.totalPages}>
          Next
        </button>
      </div>
    </Show>
  );
}
