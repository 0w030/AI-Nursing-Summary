import React from "react"
import { cn } from "../../lib/utils"

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  // 這裡模擬 Base44 的樣式邏輯
  const baseStyles = "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
  
  let variantStyles = "bg-slate-900 text-white hover:bg-slate-900/90 shadow" // default
  if (variant === "outline") variantStyles = "border border-slate-200 bg-white hover:bg-slate-100 hover:text-slate-900"
  if (variant === "ghost") variantStyles = "hover:bg-slate-100 hover:text-slate-900"
  if (variant === "secondary") variantStyles = "bg-slate-100 text-slate-900 hover:bg-slate-100/80"
  
  let sizeStyles = "h-9 px-4 py-2" // default
  if (size === "sm") sizeStyles = "h-8 rounded-md px-3 text-xs"
  if (size === "lg") sizeStyles = "h-10 rounded-md px-8"
  if (size === "icon") sizeStyles = "h-9 w-9"

  return (
    <button
      className={cn(baseStyles, variantStyles, sizeStyles, className)}
      ref={ref}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }