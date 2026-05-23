import { UZ_BANNER_SRC } from "../assets/uzSymbols";

type UzbekistanFlagProps = {
  className?: string;
  width?: number;
  height?: number;
  side?: "left" | "right";
  title?: string;
};

export default function UzbekistanFlag({
  className,
  width = 54,
  height = 36,
  side = "left",
  title = "O'zbekiston bayrog'i",
}: UzbekistanFlagProps) {
  return (
    <img
      className={className ?? "uz-flag-img"}
      src={UZ_BANNER_SRC}
      alt={title}
      title={title}
      width={width}
      height={height}
      loading="eager"
      decoding="async"
      style={{
        width,
        height,
        objectFit: "cover",
        objectPosition: side === "right" ? "right center" : "left center",
      }}
    />
  );
}
