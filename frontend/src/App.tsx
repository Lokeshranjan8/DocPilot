import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Link2, Loader2, Copy, GitPullRequest, Check, FileText, Code } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";


interface ReadmeGeneratorProps {
  onGenerate: (repoUrl: string) => Promise<string>;
}


const markdownComponents: React.ComponentProps<typeof ReactMarkdown>["components"] = {
  h1: ({ children }) => (
    <h1 className="text-xl font-semibold border-b border-border/60 pb-2 mb-4 mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-base font-semibold border-b border-border/40 pb-1.5 mb-3 mt-6">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-sm font-semibold mb-2 mt-4">{children}</h3>
  ),
  p: ({ children }) => (
    <p className="text-sm leading-relaxed text-foreground/90 mb-3">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="text-sm list-disc list-inside space-y-1 mb-3 text-foreground/85 pl-1">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="text-sm list-decimal list-inside space-y-1 mb-3 text-foreground/85 pl-1">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  code: ({ inline, children, ...props }: any) =>
    inline ? (
      <code
        className="font-mono text-[11px] bg-muted border border-border/50 rounded px-1.5 py-0.5 text-foreground/90"
        {...props}
      >
        {children}
      </code>
    ) : (
      <code className="font-mono text-[12px] leading-relaxed">{children}</code>
    ),
  pre: ({ children }) => (
    <pre className="bg-muted/60 border border-border/40 rounded-md px-4 py-3 overflow-x-auto text-[12px] leading-relaxed mb-3 font-mono">
      {children}
    </pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-border pl-3 text-sm text-muted-foreground italic mb-3">
      {children}
    </blockquote>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline underline-offset-2 hover:opacity-80 transition-opacity"
    >
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto mb-3">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="text-left text-xs font-medium text-muted-foreground border-b border-border/50 pb-2 pr-4">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="text-sm py-1.5 pr-4 border-b border-border/30 text-foreground/85">
      {children}
    </td>
  ),
  hr: () => <hr className="border-border/40 my-4" />,
};




export const App = () => {
  // const [link, setLink] = useState("");


  const handleGenerate = async (repoUrl: string): Promise<string> => {
    const response_struct = {
      method: 'POST',
      headers: {
        'Content-type': 'application/json'
      },
      body: JSON.stringify({
        repo_url: repoUrl
      })
    };

    const response = await fetch('http://localhost:8081/fetchrepo', response_struct);
    const data = await response.json();

    if (data.readme) {
      return data.readme;
    } else {
      throw new Error("No readme generated");
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-background via-background to-muted/30 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight">
            DocPilot
          </h1>
          <p className="text-muted-foreground text-sm">
            Enter a GitHub repository link to generate documentation
          </p>
        </div>

        <ReadmeGenerator onGenerate={handleGenerate} />
      </div>
    </div>
  );
};




function ReadmeGenerator({ onGenerate }: ReadmeGeneratorProps) {
  const [linkInput, setLinkInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [tab, setTab] = useState<"preview" | "raw">("preview");
  const [copied, setCopied] = useState(false);

  async function handleSubmit() {
    if (!linkInput.trim() || loading) return;
    setLoading(true);
    setResult("");
    try {
      const md = await onGenerate(linkInput.trim());
      setResult(md);
      setTab("preview");
    } catch (error) {
      setResult("Failed to generate README. Please check the repository URL.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleOpenPR() {
    const base = linkInput.trim().replace(/\/$/, "");
    window.open(`${base}/compare`, "_blank");
  }

  return (
    <div className="w-full space-y-4">
      <div className="relative group">
        <div className="absolute -inset-0.5 bg-linear-to-r from-primary/20 to-primary/5 rounded-lg blur opacity-50 group-hover:opacity-100 transition duration-500" />
        <div className="relative flex items-center gap-2 bg-card border border-border/50 rounded-lg p-2">
          <Link2 className="w-5 h-5 text-muted-foreground ml-2 shrink-0" />
          <Input
            type="url"
            placeholder="https://github.com/username/repository"
            value={linkInput}
            onChange={(e) => setLinkInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 shadow-none"
          />
          <Button
            onClick={handleSubmit}
            disabled={loading || !linkInput.trim()}
            size="sm"
            className="mr-1 shrink-0"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Generate"}
          </Button>
        </div>
      </div>

      {result && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-card border border-border/50 rounded-lg overflow-hidden">

            <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/40 bg-muted/30">
              <div className="flex items-center gap-2.5">
                <div className="flex gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-border/60" />
                  <span className="w-2.5 h-2.5 rounded-full bg-border/60" />
                  <span className="w-2.5 h-2.5 rounded-full bg-border/60" />
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <FileText className="w-3.5 h-3.5" />
                  <span className="text-xs font-mono">README.md</span>
                </div>
              </div>



              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-7 px-2.5 text-xs text-muted-foreground hover:text-foreground gap-1.5"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-green-500" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                  {copied ? "Copied!" : "Copy"}
                </Button>
                <Button
                  size="sm"
                  onClick={handleOpenPR}
                  className="h-7 px-2.5 text-xs gap-1.5 bg-green-600 hover:bg-green-700 text-white border-0"
                >
                  <GitPullRequest className="w-3.5 h-3.5" />
                  Open PR
                </Button>
              </div>
            </div>

            <div className="flex border-b border-border/40 bg-muted/20 px-4">
              {(["preview", "raw"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={cn(
                    "flex items-center gap-1.5 text-xs py-2 px-3 border-b-2 transition-colors capitalize",
                    tab === t
                      ? "border-foreground text-foreground font-medium"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  )}
                >
                  {t === "preview" ? (
                    <FileText className="w-3 h-3" />
                  ) : (
                    <Code className="w-3 h-3" />
                  )}
                  {t}
                </button>
              ))}
            </div>

            {tab === "preview" && (
              <div className="px-6 py-5 max-h-[560px] overflow-y-auto prose-sm">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {result}
                </ReactMarkdown>
              </div>
            )}

            {tab === "raw" && (
              <pre className="px-6 py-5 text-xs font-mono leading-relaxed text-muted-foreground max-h-[560px] overflow-auto whitespace-pre-wrap break-words bg-muted/10">
                {result}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

