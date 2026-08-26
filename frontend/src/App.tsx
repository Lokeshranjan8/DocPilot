import { Github } from "lucide-react";

import { Button } from "@/components/ui/button";


export const App = () => {
  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center px-5">
      <section className="w-full max-w-sm rounded-2xl border border-zinc-800 bg-zinc-950 p-8 shadow-2xl shadow-black">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-green-500 text-black">
            <Github className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Welcome to DocPilot</h1>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            Sign in to continue to your workspace.
          </p>
        </div>

        <Button
          type="button"
          className="h-11 w-full bg-green-500 text-sm font-semibold text-black hover:bg-green-400 focus-visible:ring-green-500"
        >
          <Github className="mr-2 h-4 w-4" />
          Continue with GitHub
        </Button>

        <p className="mt-5 text-center text-xs text-zinc-500">
          GitHub sign-in will be connected through Firebase.
        </p>
      </section>
    </main>
  );
};
