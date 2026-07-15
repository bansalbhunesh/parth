import type { AnchorHTMLAttributes } from "react";

type AppLinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & {
  href: string;
};

/**
 * Progressively enhanced internal navigation. The site has four small routes,
 * so native anchors avoid speculative RSC requests and retain reliable
 * navigation even before hydration or when JavaScript is unavailable.
 */
export default function AppLink({ href, ...props }: AppLinkProps) {
  return <a href={href} {...props} />;
}
