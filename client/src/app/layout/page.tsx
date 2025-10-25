"use client";

import { Textarea } from "@/components/ui/textarea";
import { useSession } from "next-auth/react";
import { useRef, useState, useEffect } from "react";
import { useIsDarkMode } from "@/hooks/useDarkMode";
import { ChartNoAxesColumnDecreasing } from "lucide-react";
import { useRouter } from "next/navigation";

interface Message {
  sender: "user" | "ai";
  text: string;
}

export default function Layout() {
  const { data: session } = useSession();
  const input = useRef<HTMLTextAreaElement>(null);
  const [check, setCheck] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const isDarkModeHook = useIsDarkMode();
  const router = useRouter();

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  useEffect(() => {
    if (!session?.accessToken) {
      router.push("/signup");
    }
  }, [session]);

  const isDarkMode = mounted ? isDarkModeHook : false;

  const handleSubmit = async () => {
    if (
      !input.current ||
      input.current.value.trim() === "" ||
      !session?.accessToken
    )
      return;

    const userMessage = input.current.value;
    input.current.value = "";
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);
    setCheck(true);

    try {
      const res = await fetch("http://localhost:8001/generate-presentation", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify({
          topic: userMessage,
          access_token: session.accessToken,
        }),
      });

      const data = await res.json();
      console.log(data);
      if (data.success && data.url) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "ai",
            text: `Here’s your Google Slides presentation 👉 [View Presentation](${data.url})`,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { sender: "ai", text: "Sorry, I couldn’t generate your slides." },
        ]);
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: "Something went wrong. Try again!" },
      ]);
    } finally {
      setCheck(false);
    }
  };

  // If not mounted, render nothing to avoid SSR mismatch
  if (!mounted) return null;

  return (
    <div
      className={`flex flex-col h-screen w-full ${
        isDarkMode ? "bg-gray-900 text-white" : "bg-gray-50 text-gray-900"
      }`}
    >
      {/* Chat Window */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`p-3 rounded-2xl max-w-xs break-words ${
                msg.sender === "user"
                  ? `${
                      isDarkMode
                        ? "bg-blue-500 text-white"
                        : "bg-blue-600 text-white"
                    } rounded-br-none`
                  : `${
                      isDarkMode
                        ? "bg-gray-700 text-gray-100"
                        : "bg-gray-200 text-gray-900"
                    } rounded-bl-none`
              }`}
            >
              {msg.text.startsWith("Here’s your Google Slides presentation") ? (
                <a
                  href={msg.text.match(/\((.*?)\)/)?.[1] || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`underline ${
                    isDarkMode ? "text-blue-300" : "text-blue-700"
                  }`}
                >
                  View Presentation
                </a>
              ) : (
                msg.text
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input Box */}
      <div
        className={`px-4 pt-4 pb-8 border-t ${
          isDarkMode
            ? "bg-gray-800 border-gray-700"
            : "bg-white border-gray-200"
        }`}
      >
        <div className="max-w-4xl mx-auto flex flex-row gap-2">
          <Textarea
            placeholder="Type your topic here..."
            className="min-h-[60px] max-h-[120px] resize-none w-full"
            ref={input}
          />
          <button
            onClick={handleSubmit}
            disabled={check}
            className={`px-4 py-2 rounded-lg ${
              check
                ? "bg-gray-400 text-gray-700"
                : isDarkMode
                ? "bg-blue-500 text-white"
                : "bg-blue-600 text-white"
            }`}
          >
            {check ? "Generating..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
