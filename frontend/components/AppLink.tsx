import NextLink from "next/link";
import type { ComponentProps } from "react";

type AppLinkProps = ComponentProps<typeof NextLink>;

/**
 * Internal navigation without speculative RSC requests. The site has four
 * small routes, so viewport prefetching adds work and has triggered rejected
 * requests in WebKit without a meaningful navigation benefit.
 */
export default function AppLink(props: AppLinkProps) {
  return <NextLink {...props} prefetch={false} />;
}
