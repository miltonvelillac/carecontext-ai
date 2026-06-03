import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon?: ReactNode;
  isLoading?: boolean;
  variant?: ButtonVariant;
};

export function Button({
  children,
  className = "",
  icon,
  isLoading = false,
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button className={`button button-${variant} ${className}`.trim()} {...props}>
      {isLoading ? <Loader2 aria-hidden="true" className="spin-icon" /> : icon}
      <span>{children}</span>
    </button>
  );
}
