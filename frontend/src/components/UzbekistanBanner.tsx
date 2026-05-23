import { UZ_BANNER_SRC } from "../assets/uzSymbols";

type UzbekistanBannerProps = {
  className?: string;
  height?: number;
  title?: string;
};

export default function UzbekistanBanner({
  className,
  height = 72,
  title = "O'zbekiston gerbi va bayrog'i",
}: UzbekistanBannerProps) {
  return (
    <img
      className={className ?? "uz-banner-img"}
      src={UZ_BANNER_SRC}
      alt={title}
      title={title}
      style={{ height }}
      loading="eager"
      decoding="async"
    />
  );
}
