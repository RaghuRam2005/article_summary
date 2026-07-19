import { cn } from "@/app/lib/utils";

function GridBackground({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden",
        className
      )}
    >
      <div
        className="absolute inset-0 [background-size:64px_64px] [background-image:linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.06)_1px,transparent_1px)]"
        style={{
          maskImage:
            "radial-gradient(ellipse 60% 60% at 50% 0%, black 10%, transparent 70%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 60% 60% at 50% 0%, black 10%, transparent 70%)",
        }}
      />
      <div
        className="absolute left-1/2 top-0 h-[36rem] w-[36rem] -translate-x-1/2 -translate-y-1/3 rounded-full opacity-40 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, var(--primary) 0%, transparent 70%)",
        }}
      />
    </div>
  );
}

export { GridBackground };
