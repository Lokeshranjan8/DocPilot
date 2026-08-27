import { useCallback, useEffect, useState } from "react";
import { Github, Loader2, LogOut } from "lucide-react";
import {
  GithubAuthProvider,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  type User,
} from "firebase/auth";

import { auth } from "@/lib/firebase";
import { Button } from "@/components/ui/button";
import { ReadmeGenerator, type ReadmeResponse } from "@/components/ReadmeGenerator";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8081";


console.log(`app url = ${apiUrl}`)


export const App = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [backendVerified, setBackendVerified] = useState(false);

  useEffect(() => onAuthStateChanged(auth, (nextUser) => {
    setUser(nextUser);
    setBackendVerified(false);
    setLoading(Boolean(nextUser));
    setMessage("");
  }), []);

  const verifyBackend = useCallback(async (currentUser: User) => {
    setMessage("");
    try {
      const token = await currentUser.getIdToken();
      const response = await fetch(`${apiUrl}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Backend did not accept this Firebase token.");
      setBackendVerified(true);
    } catch (verificationError) {
      setBackendVerified(false);
      setMessage(verificationError instanceof Error ? verificationError.message : "Verification failed.");
    }
  }, []);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    let active = true;
    void verifyBackend(user).finally(() => {
      if (active) setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [user, verifyBackend]);

  async function signIn() {
    setMessage("");
    setLoading(true);
    try {
      await signInWithPopup(auth, new GithubAuthProvider());
    } catch (signInError) {
      setMessage(signInError instanceof Error ? signInError.message : "GitHub sign-in failed.");
      setLoading(false);
    }
  }

  async function signOutUser() {
    await signOut(auth);
  }

  async function authenticatedRequest<T>(path: string, body: object): Promise<T> {
    if (!user) throw new Error("You must be signed in to use the README generator.");
    const token = await user.getIdToken();
    const response = await fetch(`${apiUrl}${path}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => null) as { detail?: string } | null;
      throw new Error(error?.detail || "The request could not be completed.");
    }
    return response.json() as Promise<T>;
  }

  function generateReadme(repoUrl: string) {
    return authenticatedRequest<ReadmeResponse>("/fetchrepo", { repo_url: repoUrl });
  }

  function reviewReadme(sessionId: string, satisfied: boolean, feedback: string) {
    return authenticatedRequest<ReadmeResponse>("/review", {
      session_id: sessionId,
      satisfied,
      feedback,
    });
  }

  if (user && backendVerified) {
    return (
      <main className="min-h-screen bg-background text-foreground px-5 py-8">
        <section className="mx-auto w-full max-w-5xl">
          <header className="mb-8 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">DocPilot</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight">README workspace</h1>
              <p className="mt-2 text-sm text-muted-foreground">Generate, review, and prepare documentation for a GitHub repository.</p>
            </div>
            <Button variant="outline" onClick={signOutUser} className="shrink-0">
              <LogOut className="mr-2 h-4 w-4" /> Sign out
            </Button>
          </header>
          <ReadmeGenerator onGenerate={generateReadme} onReview={reviewReadme} />
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center px-5">
      <section className="w-full max-w-sm rounded-2xl border border-zinc-800 bg-zinc-950 p-8 shadow-2xl shadow-black">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-green-500 text-black">
            <Github className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Welcome to DocPilot</h1>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            {user ? `Signed in as ${user.displayName || user.email || "GitHub user"}` : "Sign in to continue to your workspace."}
          </p>
        </div>

        {user ? (
          <div className="space-y-3">
            <p className="text-center text-sm text-zinc-400">{loading ? "Verifying your account..." : "Backend verification failed."}</p>
            {!loading && <Button onClick={() => void verifyBackend(user)} className="h-11 w-full bg-green-500 text-sm font-semibold text-black hover:bg-green-400">Retry verification</Button>}
            <Button variant="outline" onClick={signOutUser} className="h-11 w-full border-zinc-700 bg-transparent text-white hover:bg-zinc-900 hover:text-white">
              <LogOut className="mr-2 h-4 w-4" /> Sign out
            </Button>
          </div>
        ) : (
          <Button
            type="button"
            onClick={signIn}
            disabled={loading}
            className="h-11 w-full bg-green-500 text-sm font-semibold text-black hover:bg-green-400 focus-visible:ring-green-500"
          >
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Github className="mr-2 h-4 w-4" />}
            Continue with GitHub
          </Button>
        )}

        {message && <p className="mt-5 text-center text-xs text-zinc-400">{message}</p>}
      </section>
    </main>
  );
};
