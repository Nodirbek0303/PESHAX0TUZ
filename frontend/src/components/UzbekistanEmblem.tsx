import { UZ_EMBLEM_SRC } from "../assets/uzSymbols";

type UzbekistanEmblemProps = {
  className?: string;
  size?: number;
  title?: string;
};

export default function UzbekistanEmblem({
  className,
  size = 52,
  title = "O'zbekiston gerbi",
}: UzbekistanEmblemProps) {
  return (
    <img
      className={className ?? "uz-emblem-img"}
      src={UZ_EMBLEM_SRC}
      alt={title}
      title={title}
      width={size}
      height={size}
      loading="eager"
      decoding="async"
    />
  );
}
